from __future__ import annotations

import json

from src.llm.client import LLMMessage
from src.schemas import AnalysisPlan, FinancialQueryInput


SYSTEM_PROMPT = (
    "Eres un agente analitico financiero dentro de un TFM. "
    "Trabajas solo con datos historicos ya cargados en CSV. "
    "No haces prediccion futura, recomendacion de inversion ni analisis fundamental complejo."
)


def build_planning_messages(query_input: FinancialQueryInput, fallback_plan: AnalysisPlan) -> list[LLMMessage]:
    payload = {
        "input": query_input.to_dict(),
        "fallback_plan": fallback_plan.to_dict(),
        "required_json_schema": {
            "intent": "str",
            "metrics": ["str"],
            "plots": ["str"],
            "required_columns": ["str"],
            "textual_focus": "str",
            "agent_name": "str",
        },
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Devuelve solo JSON valido. Ajusta el plan analitico sin cambiar la intent ni inventar columnas.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]


def build_codegen_messages(plan: AnalysisPlan, deterministic_code: str) -> list[LLMMessage]:
    payload = {
        "analysis_plan": plan.to_dict(),
        "deterministic_code": deterministic_code,
        "required_json_schema": {"code": "str"},
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Devuelve solo JSON valido con un campo code. "
            "El codigo debe ser Python ejecutable, leer el payload recibido por argv[1] y escribir JSON en stdout. "
            "Si no estas seguro, conserva la estructura del codigo determinista.\n"
            f"{json.dumps(payload, ensure_ascii=False)}",
        ),
    ]


def build_interpretation_messages(output: dict, fallback_answer: str) -> list[LLMMessage]:
    payload = {
        "execution_output": output,
        "fallback_answer": fallback_answer,
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Redacta una respuesta breve en espanol para usuario final. "
            "Usa fallback_answer solo como referencia, pero no lo copies literalmente. "
            "Explica el resultado en 2 o 3 frases naturales. "
            "Respeta las metricas recibidas, no anadas datos externos, no hagas predicciones "
            "y evita recomendaciones de inversion.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]
