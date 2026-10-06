from __future__ import annotations

import importlib
import sys
from typing import Any, Mapping

from .bridge import (
    DDS_TO_SUIT,
    RANKS,
    SEATS,
    SUIT_TO_DDS,
    deal_to_pbn,
    derive_contract,
    derive_play_state,
    normalize_card,
    normalize_vulnerability,
    seat_index,
    validate_full_deal,
    vulnerability_mode,
)
from .config import Settings


class DDSError(RuntimeError):
    pass


class DDSClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self._dds3 = None

    def _load(self):
        if self._dds3 is not None:
            return self._dds3
        try:
            self._dds3 = importlib.import_module("dds3")
            return self._dds3
        except ImportError as first_error:
            candidates = [
                self.settings.ben_root / "bin" / "dds3-linux",
                self.settings.ben_root / "bin" / "dds3",
                self.settings.ben_root / "bin",
            ]
            for candidate in candidates:
                if candidate.is_dir() and str(candidate) not in sys.path:
                    sys.path.insert(0, str(candidate))
                try:
                    self._dds3 = importlib.import_module("dds3")
                    return self._dds3
                except ImportError:
                    continue
            raise DDSError(
                "DDS3 could not be imported. bridge-llm expects Python 3.12 and BEN's "
                f"vendored Linux DDS3 under {self.settings.ben_root}/bin/dds3-linux. "
                f"Original error: {first_error}"
            ) from first_error

    @staticmethod
    def _friendly_table(matrix: list[list[int]]) -> dict[str, dict[str, int]]:
        strains = ["S", "H", "D", "C", "NT"]
        return {
            strain: {seat: int(matrix[s_i][h_i]) for h_i, seat in enumerate(SEATS)}
            for s_i, strain in enumerate(strains)
        }

    def table(self, hands: Mapping[str, str], vulnerability: str | None = None) -> dict[str, Any]:
        dds3 = self._load()
        normalized = validate_full_deal(hands)
        pbn = deal_to_pbn(normalized)
        mode = vulnerability_mode(vulnerability)
        raw = dds3.calc_all_tables_pbn([pbn], mode=mode)
        tables = raw.get("tables") or []
        if not tables:
            raise DDSError("DDS3 returned no double-dummy table")
        matrix = tables[0]["res_table"]
        par_results = raw.get("par_results") or []
        return {
            "deal_pbn": pbn,
            "vulnerability": normalize_vulnerability(vulnerability),
            "table": self._friendly_table(matrix),
            "par": par_results[0] if par_results else None,
        }

    @staticmethod
    def _rank_char(rank: int) -> str:
        if rank < 2 or rank > 14:
            return str(rank)
        return {14: "A", 13: "K", 12: "Q", 11: "J", 10: "T"}.get(rank, str(rank))

    def best_card(
        self,
        hands: Mapping[str, str],
        dealer: str,
        auction: list[str],
        played: list[str] | None = None,
    ) -> dict[str, Any]:
        dds3 = self._load()
        state = derive_play_state(hands, dealer, auction, played or [])
        trump = SUIT_TO_DDS[state.contract.strain]
        trick_suit = [0, 0, 0]
        trick_rank = [0, 0, 0]
        for i, card in enumerate(state.current_trick[:3]):
            card = normalize_card(card)
            trick_suit[i] = SUIT_TO_DDS[card[0]]
            trick_rank[i] = 14 - RANKS.index(card[1])

        remaining_pbn = deal_to_pbn(state.remaining_hands, validate=False)
        raw = dds3.solve_board_pbn(
            remaining_pbn,
            trump=trump,
            first=seat_index(state.current_leader),
            current_trick_suit=tuple(trick_suit),
            current_trick_rank=tuple(trick_rank),
            target=-1,
            solutions=3,
            mode=1,
        )
        suits = list(raw.get("suit") or [])
        ranks = list(raw.get("rank") or [])
        scores = list(raw.get("score") or [])
        equals = list(raw.get("equals") or [])
        candidates = []
        count = min(len(suits), len(ranks), len(scores))
        for i in range(count):
            candidates.append({
                "card": DDS_TO_SUIT[int(suits[i])] + self._rank_char(int(ranks[i])),
                "score": int(scores[i]),
                "equals": int(equals[i]) if i < len(equals) else 0,
            })
        return {
            "contract": state.contract.text,
            "declarer": state.contract.declarer,
            "opening_leader": state.opening_leader,
            "current_leader": state.current_leader,
            "next_seat": state.next_seat,
            "current_trick": state.current_trick,
            "completed_tricks": state.completed_tricks,
            "trick_winners": state.trick_winners,
            "remaining_deal_pbn": remaining_pbn,
            "candidates": candidates,
            "raw": raw,
        }

    def analyse_play(
        self,
        hands: Mapping[str, str],
        dealer: str,
        auction: list[str],
        played: list[str],
    ) -> dict[str, Any]:
        dds3 = self._load()
        normalized = validate_full_deal(hands)
        contract = derive_contract(auction, dealer)
        if contract is None:
            raise DDSError("Auction has no contract")
        opening_leader = SEATS[(seat_index(contract.declarer) + 1) % 4]
        pbn = deal_to_pbn(normalized)
        play = "".join(normalize_card(c) for c in played)
        raw = dds3.analyse_play_pbn(
            pbn,
            play=play,
            trump=SUIT_TO_DDS[contract.strain],
            first=seat_index(opening_leader),
        )
        return {
            "contract": contract.text,
            "declarer": contract.declarer,
            "opening_leader": opening_leader,
            "played": [normalize_card(c) for c in played],
            "analysis": raw,
        }

    def probe(self) -> dict[str, Any]:
        try:
            dds3 = self._load()
            module_value = getattr(dds3, "module_name", "dds3")
            api_value = getattr(dds3, "api_root", "unknown")
            if callable(module_value):
                module_value = module_value()
            if callable(api_value):
                api_value = api_value()
            return {
                "ok": True,
                "ben_root": str(self.settings.ben_root),
                "module": str(module_value),
                "api_root": str(api_value),
            }
        except Exception as exc:
            return {"ok": False, "ben_root": str(self.settings.ben_root), "error": str(exc)}
