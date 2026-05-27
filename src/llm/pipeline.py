from __future__ import annotations

import json

from src.config import LLMConfig
from src.llm.client import LLMClientError, create_llm_client
from src.llm.prompts import (
    build_analysis_messages,
    build_codegen_messages,
    build_code_repair_messages,
    build_interpretation_messages,
)
from src.schemas import AnalysisPlan, FinancialQueryInput


MAX_LLM_ATTEMPTS = 3


def _as_str_list(value: object, default: list[str]) -> list[str]:
    if not isinstance(value, list):
        return default
    items = [str(item) for item in value if str(item).strip()]
    return items or default


def _json_from_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _code_from_text(text: str) -> str:
    try:
        payload = _json_from_text(text)
        return str(payload.get("code") or "").strip()
    except json.JSONDecodeError:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        if "def main(" in cleaned and "json.dumps" in cleaned:
            return cleaned
        raise


def build_llm_analysis(query_input: FinancialQueryInput) -> tuple[AnalysisPlan, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar LLM_API_KEY/LLM_MODEL o un perfil LLM valido.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para analisis.")
        messages = build_analysis_messages(query_input)
        last_error: Exception | None = None
        payload = None
        for attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                payload = _json_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Reintenta y devuelve exclusivamente un objeto JSON valido.",
                    )
                ]
        if payload is None:
            raise LLMClientError(str(last_error))
        return (
            AnalysisPlan(
                interpreted_intent=str(payload.get("interpreted_intent") or "").strip(),
                analysis_type=str(payload.get("analysis_type") or "").strip(),
                metrics=_as_str_list(payload.get("metrics"), []),
                required_columns=_as_str_list(payload.get("required_columns"), []),
                data_requirements=_as_str_list(payload.get("data_requirements"), []),
                output_requirements=_as_str_list(payload.get("output_requirements"), []),
                presentation_preferences=_as_str_list(payload.get("presentation_preferences"), []),
                reasoning=str(payload.get("reasoning") or "").strip(),
            ),
            [],
        )
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo interpretar la consulta con LLM: {exc}") from exc


def build_llm_code(query_input: FinancialQueryInput, plan: AnalysisPlan) -> tuple[str, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar LLM_API_KEY/LLM_MODEL o un perfil LLM valido.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para generacion de codigo.")
        messages = build_codegen_messages(query_input, plan)
        last_error: Exception | None = None
        code = ""
        for attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                code = _code_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Reintenta con un objeto JSON estricto "
                        "con un unico campo code. No uses markdown. No expliques nada.",
                    )
                ]
        if not code:
            raise LLMClientError(str(last_error))
        if "def main(" not in code or "json.dumps" not in code:
            raise LLMClientError("El codigo LLM no cumple el contrato minimo.")
        return code, []
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo generar codigo con LLM: {exc}") from exc


def repair_llm_code(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    previous_code: str,
    error_detail: str,
) -> tuple[str, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar LLM_API_KEY/LLM_MODEL o un perfil LLM valido.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para reparar codigo.")
        messages = build_code_repair_messages(query_input, plan, previous_code, error_detail)
        last_error: Exception | None = None
        code = ""
        for attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                code = _code_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La reparacion anterior no fue JSON valido. Reintenta con un objeto JSON estricto "
                        "con un unico campo code.",
                    )
                ]
        if not code:
            raise LLMClientError(str(last_error))
        if "def main(" not in code or "json.dumps" not in code:
            raise LLMClientError("El codigo reparado no cumple el contrato minimo.")
        return code, ["Se reparo codigo generado tras un error previo."]
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo reparar codigo con LLM: {exc}") from exc


def build_llm_interpretation(output: dict, plan: AnalysisPlan) -> tuple[str, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar LLM_API_KEY/LLM_MODEL o un perfil LLM valido.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para interpretacion.")
        response = client.complete_text(build_interpretation_messages(output, plan))
        answer = response.content.strip()
        if not answer:
            raise LLMClientError("El LLM devolvio una respuesta vacia.")
        return answer, []
    except LLMClientError as exc:
        raise LLMClientError(f"No se pudo obtener interpretacion LLM: {exc}") from exc
