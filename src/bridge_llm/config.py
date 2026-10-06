from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ben_url: str = "http://127.0.0.1:8085"
    ben_root: Path = Path.home() / ".local" / "share" / "bridge-llm" / "ben"
    ben_timeout: float = 120.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            ben_url=os.getenv("BEN_URL", "http://127.0.0.1:8085").rstrip("/"),
            ben_root=Path(os.path.expandvars(os.path.expanduser(os.getenv(
                "BEN_ROOT", str(Path.home() / ".local" / "share" / "bridge-llm" / "ben")
            )))),
            ben_timeout=float(os.getenv("BEN_TIMEOUT", "120")),
        )
