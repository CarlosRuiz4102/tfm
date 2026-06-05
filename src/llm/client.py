from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import LLMConfig


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    raw: Any


class LLMClientError(RuntimeError):
    pass


def _repair_mojibake(text: str) -> str:
    """Repair UTF-8 text that was decoded as latin-1/cp1252."""
    mojibake_markers = ("\u00c3", "\u00c2", "\u00e2", "\ufffd")
    if not any(marker in text for marker in mojibake_markers):
        return text
    for encoding in ("latin-1", "cp1252"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        if repaired.count("\ufffd") <= text.count("\ufffd"):
            return repaired
    return text


class OpenAICompatibleLLMClient:
    """Cliente minimo para APIs compatibles con OpenAI Chat Completions."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        if config is None:
            config = LLMConfig.from_env()
        if config.provider != "openai-compatible":
            raise LLMClientError(f"Proveedor LLM no soportado todavia: {config.provider}")
        if not config.is_configured:
            raise LLMClientError("Faltan VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para usar openai/gpt-oss-20b sobre vLLM.")
        self.config = config

        try:
            from openai import OpenAI
            import httpx
        except ImportError as exc:  # pragma: no cover - depende del entorno local
            raise LLMClientError("Falta instalar la dependencia openai.") from exc

        kwargs: dict[str, Any] = {
            "api_key": config.api_key,
            "timeout": config.timeout_seconds,
        }
        if config.base_url:
            kwargs["base_url"] = config.base_url
        if not config.verify_ssl:
            kwargs["http_client"] = httpx.Client(verify=False, timeout=config.timeout_seconds)
        self._client = OpenAI(**kwargs)

    def complete_text(self, messages: list[LLMMessage], *, response_format: dict[str, str] | None = None) -> LLMResponse:
        request: dict[str, Any] = {
            "model": self.config.model,
            "messages": [message.to_dict() for message in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if response_format is not None:
            request["response_format"] = response_format

        try:
            completion = self._client.chat.completions.create(**request)
        except TypeError:
            request.pop("response_format", None)
            completion = self._client.chat.completions.create(**request)
        except Exception as exc:  # pragma: no cover - requiere llamada real a API externa
            raise LLMClientError(f"Fallo al llamar al LLM: {exc}") from exc

        content = _repair_mojibake(completion.choices[0].message.content or "")
        return LLMResponse(content=content, model=self.config.model, raw=completion)

    def complete_json(self, messages: list[LLMMessage]) -> LLMResponse:
        return self.complete_text(messages, response_format={"type": "json_object"})


def create_llm_client(config: LLMConfig | None = None) -> OpenAICompatibleLLMClient | None:
    if config is None:
        config = LLMConfig.from_env()
    if not config.is_configured:
        return None
    return OpenAICompatibleLLMClient(config)
