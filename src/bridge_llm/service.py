from __future__ import annotations

from typing import Any, Mapping

from .ben import BenClient
from .bridge import (
    BridgeInputError,
    auction_to_ctx,
    derive_contract,
    normalize_auction,
    normalize_hand,
    normalize_scoring,
    normalize_seat,
    normalize_vulnerability,
    remove_seen_cards,
    seat_at,
)
from .config import Settings
from .dds import DDSClient


class BridgeService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self.ben = BenClient(self.settings)
        self.dds = DDSClient(self.settings)

    @staticmethod
    def _hands(payload: Mapping[str, Any]) -> dict[str, str]:
        raw = payload.get("hands") or payload.get("deal")
        if not isinstance(raw, Mapping):
            raise BridgeInputError("Expected 'hands'/'deal' object with N/E/S/W hands")
        result = {}
        for key, value in raw.items():
            seat = normalize_seat(str(key))
            result[seat] = normalize_hand(str(value))
        return result

    @staticmethod
    def _hand_for(payload: Mapping[str, Any], seat: str, played: list[str] | None = None) -> str:
        if payload.get("hand") is not None:
            return remove_seen_cards(normalize_hand(str(payload["hand"])), played)
        raw_hands = payload.get("hands") or payload.get("deal")
        if isinstance(raw_hands, Mapping):
            value = raw_hands.get(seat) or raw_hands.get(seat.lower())
            if value is not None:
                return remove_seen_cards(normalize_hand(str(value)), played)
        raise BridgeInputError(f"No hand supplied for seat {seat}")

    @staticmethod
    def _played(payload: Mapping[str, Any]) -> list[str]:
        raw = payload.get("played") or []
        if isinstance(raw, str):
            text = raw.strip().upper().replace("10", "T")
            if len(text) % 2:
                raise BridgeInputError("Concatenated 'played' string must contain 2-char cards")
            return [text[i:i + 2] for i in range(0, len(text), 2)]
        return [str(x) for x in raw]

    def run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        action = str(payload.get("action", "")).strip().lower().replace("-", "_")
        if not action:
            raise BridgeInputError("Missing 'action'")
        dispatch = {
            "bid": self.bid,
            "lead": self.lead,
            "play": self.play,
            "claim": self.claim,
            "explain_auction": self.explain_auction,
            "dd_table": self.dd_table,
            "dd_best_card": self.dd_best_card,
            "dd_analyse_play": self.dd_analyse_play,
            "dd_analyze_play": self.dd_analyse_play,
            "status": self.status,
        }
        if action not in dispatch:
            raise BridgeInputError(
                f"Unknown action {action!r}; supported: {', '.join(sorted(dispatch))}"
            )
        result = dispatch[action](payload)
        return {"ok": True, "action": action, **result}

    def _common_ben(self, payload: Mapping[str, Any]) -> tuple[str, str, str, list[str], str, bool]:
        seat = normalize_seat(str(payload["seat"]))
        dealer = normalize_seat(str(payload["dealer"]))
        vulnerability = normalize_vulnerability(payload.get("vulnerability"))
        auction = normalize_auction(payload.get("auction") or [])
        scoring = normalize_scoring(payload.get("scoring"))
        details = bool(payload.get("details", True))
        return seat, dealer, vulnerability, auction, scoring, details

    def bid(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        seat, dealer, vulnerability, auction, scoring, details = self._common_ben(payload)
        hand = self._hand_for(payload, seat)
        result = self.ben.bid(
            hand=hand, seat=seat, dealer=dealer, vul=vulnerability,
            ctx=auction_to_ctx(auction), details=details, tournament=scoring,
        )
        return {"engine": "BEN", "result": result}

    def lead(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        seat, dealer, vulnerability, auction, scoring, details = self._common_ben(payload)
        hand = self._hand_for(payload, seat)
        result = self.ben.lead(
            hand=hand, seat=seat, dealer=dealer, vul=vulnerability,
            ctx=auction_to_ctx(auction), details=details, tournament=scoring,
        )
        return {"engine": "BEN", "result": result}

    def play(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        seat, dealer, vulnerability, auction, scoring, details = self._common_ben(payload)
        played = self._played(payload)
        hand = self._hand_for(payload, seat, played)
        contract = derive_contract(auction, dealer)
        if contract is None:
            raise BridgeInputError("Auction has no contract")
        dummy_seat = seat_at(contract.declarer, 2)

        if payload.get("dummy_hand") is not None:
            other_hand = remove_seen_cards(normalize_hand(str(payload["dummy_hand"])), played)
        else:
            other_seat = contract.declarer if seat == dummy_seat else dummy_seat
            other_hand = self._hand_for(payload, other_seat, played)

        result = self.ben.play(
            hand=hand, dummy=other_hand, seat=seat, dealer=dealer, vul=vulnerability,
            ctx=auction_to_ctx(auction), played="".join(played), details=details,
            tournament=scoring,
        )
        return {
            "engine": "BEN",
            "contract": contract.text,
            "declarer": contract.declarer,
            "dummy": dummy_seat,
            "result": result,
        }

    def claim(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        seat, dealer, vulnerability, auction, _scoring, _details = self._common_ben(payload)
        played = self._played(payload)
        hand = self._hand_for(payload, seat, played)
        if payload.get("dummy_hand") is not None:
            dummy = remove_seen_cards(normalize_hand(str(payload["dummy_hand"])), played)
        else:
            contract = derive_contract(auction, dealer)
            if contract is None:
                raise BridgeInputError("Auction has no contract")
            dummy_seat = seat_at(contract.declarer, 2)
            dummy = self._hand_for(payload, dummy_seat, played)
        tricks = int(payload["tricks"])
        result = self.ben.claim(
            tricks=tricks, hand=hand, dummy=dummy, seat=seat, dealer=dealer,
            vul=vulnerability, ctx=auction_to_ctx(auction), played="".join(played),
        )
        return {"engine": "BEN", "result": result}

    def explain_auction(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        auction = normalize_auction(payload.get("auction") or [])
        return {"engine": "BEN", "result": self.ben.explain_auction(auction_to_ctx(auction))}

    def dd_table(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        result = self.dds.table(self._hands(payload), payload.get("vulnerability"))
        return {"engine": "DDS3", "result": result}

    def dd_best_card(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        result = self.dds.best_card(
            self._hands(payload),
            dealer=str(payload["dealer"]),
            auction=normalize_auction(payload.get("auction") or []),
            played=self._played(payload),
        )
        return {"engine": "DDS3", "result": result}

    def dd_analyse_play(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        result = self.dds.analyse_play(
            self._hands(payload),
            dealer=str(payload["dealer"]),
            auction=normalize_auction(payload.get("auction") or []),
            played=self._played(payload),
        )
        return {"engine": "DDS3", "result": result}

    def status(self, _payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        ben = self.ben.probe()
        dds = self.dds.probe()
        return {
            "engine": "bridge-llm",
            "result": {
                "ready": bool(ben.get("ok") and dds.get("ok")),
                "ben": ben,
                "dds": dds,
                "python_required": "3.12",
            },
        }
