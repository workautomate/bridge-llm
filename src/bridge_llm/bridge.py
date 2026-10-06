from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

SEATS = "NESW"
SUITS = "SHDC"
RANKS = "AKQJT98765432"
RANK_VALUE = {rank: 14 - i for i, rank in enumerate(RANKS)}
SUIT_TO_DDS = {"S": 0, "H": 1, "D": 2, "C": 3, "N": 4, "NT": 4}
DDS_TO_SUIT = {0: "S", 1: "H", 2: "D", 3: "C", 4: "N"}


class BridgeInputError(ValueError):
    """Raised when bridge state is internally inconsistent."""


def normalize_seat(value: str) -> str:
    seat = str(value).strip().upper()
    if seat not in SEATS:
        raise BridgeInputError(f"Invalid seat {value!r}; expected N/E/S/W")
    return seat


def seat_index(seat: str) -> int:
    return SEATS.index(normalize_seat(seat))


def seat_at(start: str, offset: int) -> str:
    return SEATS[(seat_index(start) + offset) % 4]


def normalize_hand(value: str, *, exact_cards: int | None = None) -> str:
    hand = str(value).strip().upper().replace("_", ".").replace("10", "T")
    parts = hand.split(".")
    if len(parts) != 4:
        raise BridgeInputError(
            f"Invalid hand {value!r}; expected PBN S.H.D.C with four suits"
        )
    seen: set[str] = set()
    count = 0
    for suit, ranks in zip(SUITS, parts, strict=True):
        for rank in ranks:
            if rank not in RANKS:
                raise BridgeInputError(f"Invalid rank {rank!r} in hand {value!r}")
            card = suit + rank
            if card in seen:
                raise BridgeInputError(f"Duplicate card {card} in hand {value!r}")
            seen.add(card)
            count += 1
    if exact_cards is not None and count != exact_cards:
        raise BridgeInputError(
            f"Hand {value!r} has {count} cards; expected {exact_cards}"
        )
    if count > 13:
        raise BridgeInputError(f"Hand {value!r} has more than 13 cards")
    return ".".join(parts)


def hand_to_cards(hand: str) -> set[str]:
    parts = normalize_hand(hand).split(".")
    return {
        suit + rank
        for suit, ranks in zip(SUITS, parts, strict=True)
        for rank in ranks
    }


def cards_to_hand(cards: Iterable[str]) -> str:
    grouped = {suit: [] for suit in SUITS}
    for raw in cards:
        card = normalize_card(raw)
        grouped[card[0]].append(card[1])
    for suit in SUITS:
        grouped[suit].sort(key=RANKS.index)
    return ".".join("".join(grouped[suit]) for suit in SUITS)


def normalize_card(value: str) -> str:
    text = str(value).strip().upper().replace("10", "T")
    for symbol, letter in (("♠", "S"), ("♥", "H"), ("♦", "D"), ("♣", "C")):
        text = text.replace(symbol, letter)
    if len(text) != 2 or text[0] not in SUITS or text[1] not in RANKS:
        raise BridgeInputError(
            f"Invalid card {value!r}; expected e.g. SA, HT, D2, C7"
        )
    return text


def normalize_bid(value: str) -> str:
    bid = str(value).strip().upper().replace(" ", "")
    aliases = {
        "P": "P", "PASS": "P", "--": "P", "PA": "P",
        "X": "X", "DOUBLE": "X", "DB": "X",
        "XX": "XX", "REDOUBLE": "XX", "RD": "XX",
    }
    if bid in aliases:
        return aliases[bid]
    bid = bid.replace("NT", "N")
    if len(bid) == 2 and bid[0] in "1234567" and bid[1] in "CDHSN":
        return bid
    raise BridgeInputError(f"Invalid bid {value!r}")


def normalize_auction(values: Iterable[str] | None) -> list[str]:
    if values is None:
        return []
    return [normalize_bid(v) for v in values]


def auction_to_ctx(values: Iterable[str] | None) -> str:
    """Encode auction using BEN's recommended dash-separated syntax."""
    return "-".join(normalize_auction(values))


def normalize_vulnerability(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper().replace("-", "").replace("_", "")
    aliases = {
        "": "", "NONE": "", "NO": "", "LOVE": "",
        "NS": "NS", "N/S": "NS",
        "EW": "EW", "E/W": "EW",
        "BOTH": "Both", "ALL": "Both", "B": "Both",
    }
    if text in aliases:
        return aliases[text]
    raise BridgeInputError(
        f"Invalid vulnerability {value!r}; expected NONE/NS/EW/BOTH"
    )


def vulnerability_mode(value: str | None) -> int:
    """DDS mode: 0 none, 1 both, 2 NS, 3 EW."""
    normalized = normalize_vulnerability(value)
    return {"": 0, "Both": 1, "NS": 2, "EW": 3}[normalized]


def normalize_scoring(value: str | None) -> str:
    text = str(value or "IMPS").strip().upper()
    if text in {"IMP", "IMPS"}:
        return "imps"
    if text in {"MP", "MPS", "MATCHPOINT", "MATCHPOINTS"}:
        return "mp"
    raise BridgeInputError(f"Invalid scoring {value!r}; expected IMPS or MP")


@dataclass(frozen=True)
class Contract:
    level: int
    strain: str
    declarer: str
    doubled: int = 0

    @property
    def text(self) -> str:
        suffix = "" if self.doubled == 0 else ("X" if self.doubled == 1 else "XX")
        return f"{self.level}{self.strain}{suffix}"


def derive_contract(auction: Iterable[str], dealer: str) -> Contract | None:
    calls = normalize_auction(auction)
    dealer = normalize_seat(dealer)
    last_contract: tuple[int, str, str] | None = None
    doubled = 0

    for i, call in enumerate(calls):
        seat = seat_at(dealer, i)
        if len(call) == 2 and call[0].isdigit():
            last_contract = (int(call[0]), call[1], seat)
            doubled = 0
        elif call == "X" and last_contract is not None:
            doubled = 1
        elif call == "XX" and last_contract is not None:
            doubled = 2

    if last_contract is None:
        return None

    level, strain, winning_bidder = last_contract
    winning_side = seat_index(winning_bidder) % 2
    declarer = winning_bidder
    for i, call in enumerate(calls):
        seat = seat_at(dealer, i)
        if (
            seat_index(seat) % 2 == winning_side
            and len(call) == 2
            and call[0].isdigit()
            and call[1] == strain
        ):
            declarer = seat
            break
    return Contract(level, strain, declarer, doubled)


def validate_full_deal(hands: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    all_cards: set[str] = set()
    for seat in SEATS:
        if seat not in hands:
            raise BridgeInputError(f"Full deal is missing hand for {seat}")
        hand = normalize_hand(hands[seat], exact_cards=13)
        cards = hand_to_cards(hand)
        overlap = all_cards & cards
        if overlap:
            raise BridgeInputError(f"Duplicate cards across hands: {sorted(overlap)}")
        all_cards |= cards
        normalized[seat] = hand
    if len(all_cards) != 52:
        raise BridgeInputError(f"Full deal contains {len(all_cards)} unique cards; expected 52")
    return normalized


def deal_to_pbn(hands: Mapping[str, str], *, validate: bool = True) -> str:
    normalized = validate_full_deal(hands) if validate else {
        seat: normalize_hand(hands[seat]) for seat in SEATS
    }
    return "N:" + " ".join(normalized[seat] for seat in SEATS)


def trick_winner(cards: list[str], leader: str, trump: str) -> str:
    if len(cards) != 4:
        raise BridgeInputError("A complete trick must contain exactly four cards")
    cards = [normalize_card(c) for c in cards]
    leader = normalize_seat(leader)
    trump = str(trump).upper().replace("NT", "N")
    if trump not in "SHDCN":
        raise BridgeInputError(f"Invalid trump strain {trump!r}")
    lead_suit = cards[0][0]
    winning_suit = trump if trump != "N" and any(c[0] == trump for c in cards) else lead_suit
    candidates = [
        (i, RANK_VALUE[card[1]]) for i, card in enumerate(cards) if card[0] == winning_suit
    ]
    best_i = max(candidates, key=lambda item: item[1])[0]
    return seat_at(leader, best_i)


@dataclass
class PlayState:
    contract: Contract
    opening_leader: str
    current_leader: str
    next_seat: str
    current_trick: list[str]
    completed_tricks: int
    trick_winners: list[str]
    remaining_hands: dict[str, str]


def derive_play_state(
    hands: Mapping[str, str],
    dealer: str,
    auction: Iterable[str],
    played: Iterable[str] | None,
) -> PlayState:
    normalized_hands = validate_full_deal(hands)
    contract = derive_contract(auction, dealer)
    if contract is None:
        raise BridgeInputError("Cannot analyze card play: auction has no contract")

    remaining = {seat: hand_to_cards(hand) for seat, hand in normalized_hands.items()}
    opening_leader = seat_at(contract.declarer, 1)
    leader = opening_leader
    current: list[str] = []
    winners: list[str] = []

    for raw_card in played or []:
        card = normalize_card(raw_card)
        expected = seat_at(leader, len(current))
        if card not in remaining[expected]:
            owner = next((s for s in SEATS if card in remaining[s]), None)
            if owner:
                raise BridgeInputError(
                    f"Played card {card} belongs to {owner}, but turn belongs to {expected}"
                )
            raise BridgeInputError(f"Played card {card} is not available in the remaining deal")

        if current:
            lead_suit = current[0][0]
            if card[0] != lead_suit and any(c[0] == lead_suit for c in remaining[expected]):
                raise BridgeInputError(
                    f"Illegal revoke: {expected} played {card} while still holding {lead_suit}"
                )

        remaining[expected].remove(card)
        current.append(card)
        if len(current) == 4:
            winner = trick_winner(current, leader, contract.strain)
            winners.append(winner)
            leader = winner
            current = []

    next_seat = seat_at(leader, len(current))
    return PlayState(
        contract=contract,
        opening_leader=opening_leader,
        current_leader=leader,
        next_seat=next_seat,
        current_trick=list(current),
        completed_tricks=len(winners),
        trick_winners=winners,
        remaining_hands={seat: cards_to_hand(cards) for seat, cards in remaining.items()},
    )


def remove_seen_cards(hand: str, played: Iterable[str] | None) -> str:
    cards = hand_to_cards(hand)
    for raw in played or []:
        cards.discard(normalize_card(raw))
    return cards_to_hand(cards)
