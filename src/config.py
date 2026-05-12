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

LLM_PROFILES = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "model_env": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
        "default_model": "gemini-2.5-flash",
    },
}

if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")
else:
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip().strip('"').strip("'")
            if name:
                os.environ.setdefault(name, value)


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
    profile: str
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
        profile = os.getenv("LLM_PROFILE", "").strip().lower()
        profile_config = LLM_PROFILES.get(profile, {})
        profile_api_key = os.getenv(profile_config.get("api_key_env", ""), "")
        profile_model = os.getenv(profile_config.get("model_env", ""), "")

        return cls(
            enabled=_env_bool("LLM_ENABLED", False),
            provider=os.getenv("LLM_PROVIDER", "openai-compatible"),
            profile=profile,
            base_url=os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or profile_config.get("base_url"),
            api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or profile_api_key,
            model=os.getenv("LLM_MODEL")
            or os.getenv("MODEL_NAME")
            or profile_model
            or profile_config.get("default_model", ""),
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
