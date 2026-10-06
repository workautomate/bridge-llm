# JSON request reference

All requests are JSON objects with an `action` field.

## Common notation

- Seats: `N`, `E`, `S`, `W`.
- Hands: PBN suit order `S.H.D.C`, for example `AK97543.K.T3.AK7`.
- Cards: `SA`, `HK`, `DT`, `C2`; `S10` is also accepted.
- Bids: `1C` ... `7NT`, `PASS`, `X`/`DOUBLE`, `XX`/`REDOUBLE`.
- Vulnerability: `NONE`, `NS`, `EW`, `BOTH`.
- Scoring: `IMPS` or `MP`.
- `played`: chronological card list from the opening lead onward.

## `bid`

```json
{
  "action": "bid",
  "hand": "AK97543.K.T3.AK7",
  "seat": "S",
  "dealer": "N",
  "vulnerability": "NONE",
  "auction": ["PASS", "PASS"],
  "scoring": "IMPS",
  "details": true
}
```

Instead of `hand`, `hands` may contain the acting seat.

## `lead`

```json
{
  "action": "lead",
  "hand": "KJ53.KJ7.AT92.K5",
  "seat": "W",
  "dealer": "N",
  "vulnerability": "NS",
  "auction": ["1NT", "PASS", "3NT", "PASS", "PASS", "PASS"],
  "scoring": "MP",
  "details": true
}
```

## `play`

`hands` only needs to contain the information BEN legitimately needs: the acting hand plus the visible partner hand. For declarer/defenders this is normally the dummy; when the acting seat is dummy, supply declarer's hand too.

```json
{
  "action": "play",
  "seat": "S",
  "dealer": "N",
  "vulnerability": "NONE",
  "auction": ["PASS", "PASS", "1S", "PASS", "4S", "PASS", "PASS", "PASS"],
  "hands": {
    "S": "AK97543.K.T3.AK7",
    "N": "QJ87.A95.K63.T42"
  },
  "played": ["DJ", "DK", "D3", "D2"],
  "scoring": "IMPS",
  "details": true
}
```

If your caller already has the exact BEN companion-hand parameter, it can pass `dummy_hand` explicitly.

## `claim`

```json
{
  "action": "claim",
  "tricks": 8,
  "seat": "S",
  "dealer": "N",
  "vulnerability": "NONE",
  "auction": ["1S", "PASS", "4S", "PASS", "PASS", "PASS"],
  "hand": "AK97.K.T3.AK7",
  "dummy_hand": "QJ87.A95.K63.T42",
  "played": ["DJ", "DK", "D3", "D2"]
}
```

## `explain_auction`

```json
{
  "action": "explain_auction",
  "auction": ["1NT", "PASS", "2C", "PASS", "2S"]
}
```

## `dd_table`

Requires all four original 13-card hands.

```json
{
  "action": "dd_table",
  "vulnerability": "NONE",
  "deal": {
    "N": "QJ6.K652.J85.T98",
    "E": "873.J97.AT764.Q4",
    "S": "K5.T83.KQ9.A7652",
    "W": "AT942.AQ4.32.KJ3"
  }
}
```

The result contains a friendly 5x4 trick table plus DDS par information.

## `dd_best_card`

Requires the original ful deal. `bridge-llm` reconstructs the current state from `played`.

```json
{
  "action": "dd_best_card",
  "dealer": "N",
  "auction": ["1H", "PASS", "2H", "PASS", "PASS", "PASS"],
  "played": ["D4", "DK", "D2", "DJ"],
  "deal": {
    "N": "QJ6.K652.J85.T98",
    "E": "873.J97.AT764.Q4",
    "S": "K5.T83.KQ9.A7652",
    "W": "AT942.AQ4.32.KJ3"
  }
}
```

The result includes derived contract/declarer/leader/next seat and DDS candidate cards.

## `dd_analyse_play`

```json
{
  "action": "dd_analyse_play",
  "dealer": "N",
  "auction": ["1H", "PASS", "2H", "PASS", "PASS", "PASS"],
  "played": ["D4", "DK", "D2", "DJ", "S5"],
  "deal": {
    "N": "QJ6.K652.J85.T98",
    "E": "873.J97.AT764.Q4",
    "S": "K5.T83.KQ9.A7652",
    "W": "AT942.AQ4.32.KJ3"
  }
}
```

## `status`

```json
{"action": "status"}
```

Checks BEN connectivity and DDS3 importability.
