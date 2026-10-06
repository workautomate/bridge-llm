from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .bridge import BridgeInputError
from .service import BridgeService


def _read_payload(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise BridgeInputError("Top-level JSON value must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="bridge-llm",
        description="Run BEN/DDS3 bridge analysis from a JSON request.",
    )
    parser.add_argument("input", nargs="?", help="JSON file path, or '-' for stdin")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    if not args.input:
        parser.error("input JSON file is required (or '-' for stdin)")

    try:
        payload = _read_payload(args.input)
        response = BridgeService().run(payload)
        print(json.dumps(
            response,
            ensure_ascii=False,
            indent=None if args.compact else 2,
            separators=(",", ":") if args.compact else None,
            default=str,
        ))
        return 0
    except Exception as exc:
        response = {"ok": False, "error": type(exc).__name__, "message": str(exc)}
        print(json.dumps(response, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
