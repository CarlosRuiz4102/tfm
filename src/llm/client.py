from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import LLM_CONFIG, LLMConfig


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
    """Repara UTF-8 interpretado accidentalmente como latin-1/cp1252."""
    mojibake_markers = ("Ã", "Â", "â€", "â†", "�")
    if not any(marker in text for marker in mojibake_markers):
        return text
    for encoding in ("latin-1", "cp1252"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        if repaired.count("�") <= text.count("�"):
            return repaired
    return text


class OpenAICompatibleLLMClient:
    """Cliente minimo para APIs compatibles con OpenAI Chat Completions."""

    def __init__(self, config: LLMConfig = LLM_CONFIG) -> None:
        if config.provider != "openai-compatible":
            raise LLMClientError(f"Proveedor LLM no soportado todavia: {config.provider}")
        if not config.is_configured:
            raise LLMClientError("LLM activado pero faltan LLM_API_KEY/LLM_MODEL.")
        self.config = config

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depende del entorno local
            raise LLMClientError("Falta instalar la dependencia openai.") from exc

        kwargs: dict[str, Any] = {
            "api_key": config.api_key,
            "timeout": config.timeout_seconds,
        }
        if config.base_url:
            kwargs["base_url"] = config.base_url
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


def create_llm_client(config: LLMConfig = LLM_CONFIG) -> OpenAICompatibleLLMClient | None:
    if not config.is_configured:
        return None
    return OpenAICompatibleLLMClient(config)
