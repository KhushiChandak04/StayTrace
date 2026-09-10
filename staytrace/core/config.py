from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    backend: str
    geniex_model: str
    geniex_device_map: str

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(os.getenv("STAYTRACE_DATA_DIR", "storage"))
        return cls(
            data_dir=root,
            backend=os.getenv("STAYTRACE_AI_BACKEND", "auto").lower(),
            geniex_model=os.getenv("STAYTRACE_GENIEX_MODEL", "ai-hub-models/Qwen3-VL-4B-Instruct"),
            geniex_device_map=os.getenv("STAYTRACE_GENIEX_DEVICE_MAP", "qairt"),
        )

    def ensure_dirs(self) -> None:
        for sub in ("db", "media", "reports", "benchmarks"):
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)
