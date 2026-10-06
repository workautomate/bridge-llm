# bridge-llm

`bridge-llm` is a local bridge analysis service for **Windows + WSL2**. It combines:

- **BEN (Bridge Engine)** for practical bidding, opening-lead and card-play recommendations based on the information a player is allowed to know.
- **DDS3 (Double Dummy Solver)** for full-information verification, par tables and theoretical best-card analysis.
- A **JSON CLI** that works without any LLM.
- A **Model Context Protocol (MCP) server** so Pi, Claude, Codex, Gemini or another agent can call the same engine.

Image recognition is intentionally out of scope. The caller supplies structured JSON.

## Architecture

```text
JSON file / stdin                MCP host
      |                             |
      v                             v
 bridge-llm CLI                bridge-mcp
      \_____________________________/
                    |
              BridgeService
              /           \
             v             v
      BEN REST API       DDS3 Python API
      127.0.0.1:8085     (vendored by BEN)
             \             /
              \___________/
                    |
               WSL Ubuntu 24.04
```

BEN and DDS do the bridge calculation. An LLM is optional and is best used for conversation, explanation and orchestration rather than replacing the bridge engines.

## Requirements

The supported deployment target is:

- Windows 10/11 with WSL2
- **Ubuntu 24.04** inside WSL
- Python **3.12**

Ubuntu 24.04 matters because BEN currently vendors a DDS3 Linux extension built for Python 3.12 and glibc >= 2.38.

## Install on WSL

Clone this repository inside WSL or access the checkout through `/mnt/c/...`, then run:

```bash
cd bridge-llm
bash scripts/setup_wsl.sh
```

The installer:

1. clones/updates BEN under `~/.local/share/bridge-llm/ben`;
2. runs BEN's official `setup_linux.sh`;
3. uses BEN's Python 3.12 environment at `~/ben`;
4. installs `bridge-llm` into that environment;
5. writes runtime variables to `~/.config/bridge-llm/env`.

Load the environment in a shell:

```bash
source ~/.config/bridge-llm/env
```

## Start BEN

Foreground:

```bash
scripts/start_ben.sh
```

Or let the MCP launcher start BEN automatically in the background:

```bash
scripts/run_mcp_with_ben.sh
```

Stop a BEN instance started by `ensure_ben.sh` / `run_mcp_with_ben.sh`:

```bash
scripts/stop_ben.sh
```

Check both engines:

```bash
source ~/.config/bridge-llm/env
~/ben/bin/bridge-doctor
```

## JSON CLI

Run a request from a file:

```bash
~/ben/bin/bridge-llm examples/bid.json
~/ben/bin/bridge-llm examples/dd_table.json
```

Or from stdin:

```bash
cat examples/dd_best_card.json | ~/ben/bin/bridge-llm -
```

Success responses always use an envelope like:

```json
{
  "ok": true,
  "action": "bid",
  "engine": "BEN",
  "result": {}
}
```

Errors are emitted as JSON to stderr with a non-zero exit code.

## Supported actions

| Action | Engine | Purpose |
|---|---|---|
| `bid` | BEN | Recommend a bid |
| `lead` | BEN | Recommend the opening lead |
| `play` | BEN | Recommend the next card with normal hidden information |
| `claim` | BEN/DDS internally | Check a claim |
| `explain_auction` | BEN | Explain the auction |
| `dd_table` | DDS3 | Full double-dummy table + par |
| `dd_best_card` | DDS3 | Rank legal cards in the current full-information position |
| `dd_analyse_play` | DDS3 | Analyze a complete play sequence |
| `status` | Both | Health/installation check |

See [docs/JSON_SCHEMA.md](docs/JSON_SCHEMA.md) for request formats.

## Human-friendly JSON

You do not need to use BEN's compact URL encodings. Write:

```json
{
  "action": "bid",
  "hand": "AK97543.K.T3.AK7",
  "seat": "S",
  "dealer": "N",
  "vulnerability": "NS",
  "auction": ["PASS", "1NT", "PASS", "2C"],
  "scoring": "IMPS"
}
```

The wrapper converts this to BEN's expected format (`1N`, dash-separated context, absolute vulnerability strings, etc.).

Cards use `SA`, `HK`, `DT`, `C2`. `S10` is accepted and normalized to `ST`.

## DDS state reconstruction

For DDS actions, give all four original 13-card hands plus the auction and chronological `played` cards. The program derives:

- final contract and declarer;
- opening leader;
- each completed trick winner;
- current trick leader;
- whose turn it is;
- remaining cards in every hand.

It also rejects inconsistent turns and revokes before calling DDS.

Example:

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

**DDS is double-dummy:** it sees all four hands. Use it for verification, post-mortem analysis and theoretical best play, not as a fair hidden-information opponent.

## MCP

The MCP server uses stdio by default:

```bash
source ~/.config/bridge-llm/env
~/ben/bin/bridge-mcp
```

Exposed tools:

- `bridge_run`
- `recommend_bid`
- `recommend_lead`
- `recommend_play`
- `double_dummy_table`
- `double_dummy_best_card`
- `double_dummy_analyse_play`
- `bridge_status`

### Host running inside WSL

Use the launcher so BEN is automatically available:

```json
{
  "mcpServers": {
    "bridge": {
      "command": "/absolute/path/to/bridge-llm/scripts/run_mcp_with_ben.sh"
    }
  }
}
```

### Windows host launching the WSL MCP server

A Windows-side MCP host can invoke WSL directly:

```json
{
  "mcpServers": {
    "bridge": {
      "command": "wsl.exe",
      "args": [
        "-d",
        "Ubuntu-24.04",
        "--",
        "bash",
        "-lc",
        "/absolute/wsl/path/to/bridge-llm/scripts/run_mcp_with_ben.sh"
      ]
    }
  }
}
```

Use the actual WSL path of this repository. The launcher writes BEN logs to `~/.cache/bridge-llm/ben.log`; it never writes startup text to stdout because stdout is reserved for MCP protocol messages.

## Configuration

Environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `BEN_URL` | `http://127.0.0.1:8085` | BEN REST API URL |
| `BEN_ROOT` | `~/.local/share/bridge-llm/ben` | BEN source checkout |
| `BEN_TIMEOUT` | `120` | BEN HTTP request timeout in seconds |
| `BEN_VENV` | `~/ben` | Python environment created by BEN setup |

By default BEN only binds to localhost. Keep it that way unless you deliberately add authentication/reverse proxying.

## Development

Core state logic has no third-party dependency, so it can be tested directly:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src
```

CI runs the same tests on Ubuntu 24.04 / Python 3.12.

## Upstream engines

This project is an integration layer and does not vendor BEN or DDS source code. `setup_wsl.sh` retrieves BEN separately. BEN itself uses DDS3 for its internal simulations; this project additionally exposes DDS3 directly for explicit double-dummy analysis.
