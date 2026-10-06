from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import Settings


class BenError(RuntimeError):
    pass


class BenClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()

    def get(self, endpoint: str, params: dict[str, Any]) -> Any:
        query = urllib.parse.urlencode(
            {k: str(v).lower() if isinstance(v, bool) else v for k, v in params.items()}
        )
        url = f"{self.settings.ben_url}/{endpoint.lstrip('/')}?{query}"
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.settings.ben_timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BenError(f"BEN HTTP {exc.code}: {body or exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise BenError(
                f"Cannot reach BEN at {self.settings.ben_url}: {exc.reason}. "
                "Start it with scripts/start_ben.sh."
            ) from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BenError(f"BEN returned non-JSON response: {raw[:500]!r}") from exc

    def bid(self, **params: Any) -> Any:
        return self.get("bid", params)

    def lead(self, **params: Any) -> Any:
        return self.get("lead", params)

    def play(self, **params: Any) -> Any:
        return self.get("play", params)

    def claim(self, **params: Any) -> Any:
        return self.get("claim", params)

    def explain_auction(self, ctx: str) -> Any:
        return self.get("explain_auction", {"ctx": ctx})

    def probe(self) -> dict[str, Any]:
        try:
            result = self.get("bids", {"ctx": ""})
            return {"ok": True, "url": self.settings.ben_url, "response_type": type(result).__name__}
        except Exception as exc:
            return {"ok": False, "url": self.settings.ben_url, "error": str(exc)}
