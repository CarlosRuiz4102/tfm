from __future__ import annotations

import json

from src.config import LLMConfig
from src.llm.client import LLMClientError, create_llm_client
from src.llm.prompts import build_codegen_messages, build_interpretation_messages, build_planning_messages
from src.schemas import AnalysisPlan, FinancialQueryInput


def _as_str_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    items = [str(item) for item in value if str(item).strip()]
    return items or fallback


def _json_from_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def maybe_build_llm_plan(query_input: FinancialQueryInput, fallback_plan: AnalysisPlan) -> tuple[AnalysisPlan, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.enabled or not llm_config.use_for_planning:
        return fallback_plan, []
    if not llm_config.is_configured:
        return fallback_plan, ["LLM planning activado, pero falta configurar LLM_API_KEY o LLM_MODEL."]

    try:
        client = create_llm_client(llm_config)
        if client is None:
            return fallback_plan, ["No se pudo crear el cliente LLM; se usa plan determinista."]
        response = client.complete_json(build_planning_messages(query_input, fallback_plan))
        payload = _json_from_text(response.content)
        intent = str(payload.get("intent") or fallback_plan.intent)
        if intent != fallback_plan.intent:
            return fallback_plan, ["El LLM intento cambiar la intent; se usa plan determinista."]
        return (
            AnalysisPlan(
                intent=intent,
                metrics=_as_str_list(payload.get("metrics"), fallback_plan.metrics),
                plots=_as_str_list(payload.get("plots"), fallback_plan.plots),
                required_columns=_as_str_list(payload.get("required_columns"), fallback_plan.required_columns),
                textual_focus=str(payload.get("textual_focus") or fallback_plan.textual_focus),
                agent_name=str(payload.get("agent_name") or fallback_plan.agent_name),
            ),
            [],
        )
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return fallback_plan, [f"Fallo en planning LLM; se usa plan determinista: {exc}"]


def maybe_build_llm_code(plan: AnalysisPlan, deterministic_code: str) -> tuple[str, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.enabled or not llm_config.use_for_codegen:
        return deterministic_code, []
    if not llm_config.is_configured:
        return deterministic_code, ["LLM codegen activado, pero falta configurar LLM_API_KEY o LLM_MODEL."]

    try:
        client = create_llm_client(llm_config)
        if client is None:
            return deterministic_code, ["No se pudo crear el cliente LLM; se usa codigo determinista."]
        response = client.complete_json(build_codegen_messages(plan, deterministic_code))
        payload = _json_from_text(response.content)
        code = str(payload.get("code") or "").strip()
        if "def main(" not in code or "json.dumps" not in code:
            return deterministic_code, ["El codigo LLM no cumple el contrato minimo; se usa codigo determinista."]
        return code, []
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return deterministic_code, [f"Fallo en codegen LLM; se usa codigo determinista: {exc}"]


def maybe_build_llm_interpretation(output: dict, fallback_answer: str) -> tuple[str, list[str]]:
    llm_config = LLMConfig.from_env()
    if not llm_config.enabled or not llm_config.use_for_interpretation:
        return fallback_answer, []
    if not llm_config.is_configured:
        return fallback_answer, ["LLM interpretation activado, pero falta configurar LLM_API_KEY o LLM_MODEL."]

    try:
        client = create_llm_client(llm_config)
        if client is None:
            return fallback_answer, ["No se pudo crear el cliente LLM; se usa interpretacion determinista."]
        response = client.complete_text(build_interpretation_messages(output, fallback_answer))
        answer = response.content.strip()
        return answer or fallback_answer, []
    except LLMClientError as exc:
        return fallback_answer, [f"Fallo en interpretacion LLM; se usa respuesta determinista: {exc}"]
