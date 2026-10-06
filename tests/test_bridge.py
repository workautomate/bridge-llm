import unittest

from bridge_llm.bridge import (
    auction_to_ctx,
    derive_contract,
    derive_play_state,
    normalize_bid,
    normalize_hand,
    trick_winner,
)


DEAL = {
    "N": "QJ6.K652.J85.T98",
    "E": "873.J97.AT764.Q4",
    "S": "K5.T83.KQ9.A7652",
    "W": "AT942.AQ4.32.KJ3",
}


class BridgeTests(unittest.TestCase):
    def test_normalize_bid(self):
        self.assertEqual(normalize_bid("1NT"), "1N")
        self.assertEqual(normalize_bid("pass"), "P")
        self.assertEqual(normalize_bid("double"), "X")

    def test_ctx_uses_dash_separated_format(self):
        self.assertEqual(auction_to_ctx(["1NT", "pass", "2C", "pass"]), "1N-P-2C-P")

    def test_hand_format(self):
        self.assertEqual(normalize_hand("AKQ_JT9_876_5432"), "AKQ.JT9.876.5432")

    def test_declarer_is_first_partnership_bidder_of_final_strain(self):
        contract = derive_contract(["1C", "P", "1H", "P", "2H", "P", "4H", "P", "P", "P"], "N")
        self.assertIsNotNone(contract)
        self.assertEqual(contract.strain, "H")
        self.assertEqual(contract.declarer, "S")
        self.assertEqual(contract.text, "4H")

    def test_trick_winner_with_trump(self):
        self.assertEqual(trick_winner(["SA", "S2", "H2", "SK"], "N", "H"), "S")

    def test_play_state_tracks_winner_and_next_seat(self):
        state = derive_play_state(
            DEAL,
            "N",
            ["1H", "P", "2H", "P", "P", "P"],
            ["D4", "DK", "D2", "DJ"],
        )
        self.assertEqual(state.opening_leader, "E")
        self.assertEqual(state.trick_winners, ["S"])
        self.assertEqual(state.next_seat, "S")
        self.assertNotIn("K", state.remaining_hands["S"].split(".")[2])


if __name__ == "__main__":
    unittest.main()
