from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv es opcional en ejecuciones minimas
    load_dotenv = None


# Rutas base del proyecto. Se centralizan aqui para que todos los modulos
# compartan la misma convencion de carpetas al leer y escribir artefactos.
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_CODE_DIR = RESULTS_DIR / "code"
RESULTS_LOGS_DIR = RESULTS_DIR / "logs"
RESULTS_DATA_REQUESTS_DIR = RESULTS_DIR / "data_requests"
RESULTS_DATA_RAW_DIR = RESULTS_DIR / "data_raw"
RESULTS_DATA_NORMALIZED_DIR = RESULTS_DIR / "data_normalized"

DEFAULT_OPENAI_MODEL = "openai/gpt-oss-20b"

if load_dotenv is not None:
    # En desarrollo preferimos cargar automaticamente el .env del repositorio.
    load_dotenv(ROOT_DIR / ".env")
else:
    # Fallback minimo por si python-dotenv no esta instalado.
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


def _env_int(name: str, default: int) -> int:
    # Helper pequeno para evitar repetir parseos de enteros en la configuracion.
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    # Igual que _env_int, pero pensado para temperatura y otros floats.
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return float(value)


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuracion de ejecucion del codigo Python generado por el flujo."""

    python_executable: str = sys.executable
    timeout_seconds: int = 60


@dataclass(frozen=True)
class LLMConfig:
    """Configuracion normalizada del proveedor LLM para todo el proyecto."""

    provider: str
    profile: str
    base_url: str | None
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    verify_ssl: bool

    @classmethod
    def from_env(cls) -> "LLMConfig":
        # Permitimos varios aliases porque en el proyecto se contemplan
        # entornos OpenAI, vLLM local y despliegues de universidad.
        verify_ssl_value = os.getenv("OPENAI_VERIFY_SSL") or os.getenv("LLM_VERIFY_SSL")

        return cls(
            provider=os.getenv("LLM_PROVIDER", "openai-compatible"),
            profile="openai",
            base_url=os.getenv("VLLM_BASE_URL")
            or os.getenv("UNIVERSITY_BASE_URL")
            or os.getenv("LLM_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or None,
            api_key=os.getenv("VLLM_API_KEY")
            or os.getenv("UNIVERSITY_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or "",
            model=os.getenv("VLLM_MODEL")
            or os.getenv("UNIVERSITY_MODEL")
            or os.getenv("LLM_MODEL")
            or os.getenv("OPENAI_MODEL")
            or os.getenv("MODEL_NAME")
            or DEFAULT_OPENAI_MODEL,
            temperature=_env_float("LLM_TEMPERATURE", 0.1),
            max_tokens=_env_int("LLM_MAX_TOKENS", 4096),
            timeout_seconds=_env_int("LLM_TIMEOUT_SECONDS", 120),
            verify_ssl=verify_ssl_value is None or verify_ssl_value.strip().lower() not in {"0", "false", "no", "n", "off"},
        )

    @property
    def is_configured(self) -> bool:
        # Consideramos "no configurado" tanto un valor vacio como claves de ejemplo.
        api_key = self.api_key.strip()
        model = self.model.strip()
        placeholder_keys = {
            "your_openai_key_here",
            "your_vllm_key_here",
            "tu_clave_openai",
            "tu_clave_vllm",
        }
        return bool(api_key) and api_key not in placeholder_keys and bool(model)


EXECUTION_CONFIG = ExecutionConfig()
LLM_CONFIG = LLMConfig.from_env()
