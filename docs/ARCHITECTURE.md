# Architecture

## Design goals

1. Bridge calculation must work without an LLM.
2. BEN remains the primary hidden-information playing engine.
3. DDS3 is explicitly labeled double-dummy and is used for verification/full-information analysis.
4. CLI and MCP use one service layer so results cannot drift between interfaces.
5. BEN is kept as an external upstream checkout rather than copied into this repository.

## Components

### `bridge.py`

Pure bridge-state logic and validation: hand/card/bid normalization, contract/declarer derivation, trick winners, legal-turn checks and state reconstruction.

### `ben.py`

Small stateless HTTP client for BEN `gameapi.py`.

### `dds.py`

Loads `dds3` from the active environment or BEN's vendored `bin/dds3-linux` package and exposes DD table, best-card and play-analysis helpers.

### `service.py`

Canonical action dispatcher. Both CLI and MCP call this layer.

### `cli.py`

Reads one JSON object from a file/stdin and prints one JSON result.

### `mcp_server.py`

MCP v2 stdio server. Tools are thin adapters over `BridgeService`.

## Information boundaries

BEN calls only receive the acting hand pltÈ[™›Ü›X][Ûˆš\ÚX›H]HX›KˆÈØ[È™\]Z\™H[›İ\ˆ[™È[™\™H[X™\˜][H˜[YYİX›WÙ[[^WÊ˜ÈXZÙHZ\ˆ[Z[™›Ü›X][Ûˆ˜]\™H^XÚ]‚‚ˆÈÈ›ØÙ\ÜÈ[Ù[ÛˆÔÓ‚‘Sˆ\ÈHÛ™Ë\[›š[™ÈØØ[‘TÕ›ØÙ\ÜÈÛˆLËŒŒŒNXˆÈ[œÈ[‹\›ØÙ\ÜÈ[œÚYHœšYÙK[XˆHPÔ›ØÙ\ÜÈØ[ˆ™HÚÜ[]™YÜˆÜİ[X[˜YÙYˆ[—ÛXÜİÚ]Ø™[‹œÚİ\È‘SˆÛ›HÚ[ˆ™XÙ\ÜØ\H[™™\Ù\™\Èİİ]^Û\Ú]™[H›ÜˆPÔ‚