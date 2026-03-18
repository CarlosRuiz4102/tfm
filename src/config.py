from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_CODE_DIR = RESULTS_DIR / "code"
RESULTS_LOGS_DIR = RESULTS_DIR / "logs"


@dataclass(frozen=True)
class ExecutionConfig:
    python_executable: str = "python"
    timeout_seconds: int = 60


EXECUTION_CONFIG = ExecutionConfig()
