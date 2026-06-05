from __future__ import annotations

from pathlib import Path


def csv_exists(csv_path: str) -> bool:
    return Path(csv_path).exists()
