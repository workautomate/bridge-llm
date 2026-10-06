from __future__ import annotations

import json

from .service import BridgeService


def main() -> int:
    result = BridgeService().status({})
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result["result"]["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
