from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv es opcional en ejecuciones minimas
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_CODE_DIR = RESULTS_DIR / "code"
RESULTS_LOGS_DIR = RESULTS_DIR / "logs"

if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return float(value)


@dataclass(frozen=True)
class ExecutionConfig:
    python_executable: str = "python"
    timeout_seconds: int = 60


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool
    provider: str
    base_url: str | None
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    use_for_planning: bool
    use_for_codegen: bool
    use_for_interpretation: bool

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            enabled=_env_bool("LLM_ENABLED", False),
            provider=os.getenv("LLM_PROVIDER", "openai-compatible"),
            base_url=os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("LLM_MODEL") or os.getenv("MODEL_NAME", ""),
            temperature=_env_float("LLM_TEMPERATURE", 0.1),
            max_tokens=_env_int("LLM_MAX_TOKENS", 2048),
            timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", 60),
            use_for_planning=_env_bool("LLM_USE_FOR_PLANNING", False),
            use_for_codegen=_env_bool("LLM_USE_FOR_CODEGEN", False),
            use_for_interpretation=_env_bool("LLM_USE_FOR_INTERPRETATION", False),
        )

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key.strip()) and bool(self.model.strip())


EXECUTION_CONFIG = ExecutionConfig()
LLM_CONFIG = LLMConfig.from_env()
