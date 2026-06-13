from __future__ import annotations

import json
from typing import Any

from src.llm.client import LLMMessage
from src.schemas import AnalysisPlan, FinancialDataRequest, FinancialQueryInput


DATA_SYSTEM_PROMPT = (
    "Eres un componente de planificacion y correccion de peticiones de datos financieros historicos. "
    "Tu objetivo es producir JSON valido, trazable y utilizable por codigo. "
    "No calculas metricas financieras, no interpretas resultados y no redactas respuestas finales."
)

ANALYSIS_SYSTEM_PROMPT = (
    "Eres un componente profesional de analisis financiero historico asistido por LLM. "
    "Trabajas exclusivamente con datos historicos ya descargados y con el contrato JSON indicado. "
    "No realizas predicciones, asesoramiento de inversion, recomendaciones de compra/venta, "
    "analisis fundamental externo ni incorporas informacion que no este en la entrada."
)

ANALYSIS_TYPE_CATALOG = [
    "historical_overview",
    "historical_return_analysis",
    "comparative_return_analysis",
    "volatility_analysis",
    "drawdown_analysis",
    "technical_indicator_analysis",
    "risk_return_profile",
]


def build_data_request_messages(query_input: FinancialQueryInput) -> list[LLMMessage]:
    """Prompt del Agente 1: convertir consulta libre en contrato de datos."""
    payload = {
        "input": query_input.to_dict(),
        "required_json_schema": {
            "user_query": "str",
            "provider": "yfinance",
            "instruments": [{"ticker": "str"}],
            "interval": "str",
            "start": "YYYY-MM-DD o null",
            "end": "YYYY-MM-DD o null",
            "period": "str o null",
            "required_fields": ["str"],
            "needs_clarification": "bool",
            "clarification_reason": "str o null",
        },
    }
    return [
        LLMMessage("system", DATA_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Agente 1 - PLANIFICADOR DE DATOS.\n"
            "Convierte la consulta del usuario en un FinancialDataRequest JSON valido. "
            "Devuelve exclusivamente JSON, sin markdown ni texto adicional.\n"
            "Tu trabajo es decidir que datos hay que pedir, no hacer el analisis financiero.\n"
            "Debes:\n"
            "1. Identificar instrumentos o tickers.\n"
            "2. Inferir intervalo temporal y usar period o start/end segun corresponda.\n"
            "3. Mantener provider='yfinance'.\n"
            "4. Incluir required_fields con Open, High, Low, Close, Adj Close y Volume.\n"
            "5. Marcar needs_clarification=true si la consulta no permite una descarga fiable.\n"
            "No debes calcular metricas, razonar sobre rentabilidad ni proponer respuesta final.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]


def build_data_request_repair_messages(
    query_input: FinancialQueryInput,
    previous_request: FinancialDataRequest,
    validation_errors: list[str],
    stage: str,
) -> list[LLMMessage]:
    """Prompt compartido para las dos rutas de reparacion de la fase de datos."""
    prompt_title = "Subagente 1 - CORRECCION ESTRUCTURAL" if stage == "structural" else "Subagente 2 - CORRECCION OPERATIVA"
    stage_guidance = (
        "Corrige problemas de estructura, contrato, fechas, intervalos o instrumentos vacios."
        if stage == "structural"
        else "Corrige el request para que la descarga real en yfinance sea util sin cambiar libremente la intencion del usuario."
    )
    payload = {
        "input": query_input.to_dict(),
        "previous_financial_data_request": previous_request.to_dict(),
        "validation_errors": validation_errors,
        "required_json_schema": {
            "user_query": "str",
            "provider": "yfinance",
            "instruments": [{"ticker": "str"}],
            "interval": "str",
            "start": "YYYY-MM-DD o null",
            "end": "YYYY-MM-DD o null",
            "period": "str o null",
            "required_fields": ["str"],
            "needs_clarification": "bool",
            "clarification_reason": "str o null",
        },
    }
    return [
        LLMMessage("system", DATA_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            f"{prompt_title}.\n"
            "Devuelve exclusivamente un FinancialDataRequest JSON valido.\n"
            f"{stage_guidance}\n"
            "Si no puedes corregir el problema de forma fiable, marca needs_clarification=true "
            "y explica brevemente el motivo en clarification_reason.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]


def build_analysis_messages(query_input: FinancialQueryInput, input_payload: dict[str, Any] | None = None) -> list[LLMMessage]:
    """Prompt del Agente 2: planificar el analisis sobre datos ya descargados."""
    current_input = input_payload or query_input.to_dict()
    payload = {
        "input": current_input,
        "analysis_type_catalog": ANALYSIS_TYPE_CATALOG,
        "available_dataset_columns": (
            ((current_input.get("data_context") or {}).get("available_columns"))
            or ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        ),
        "quality_guidelines": {
            "simple_queries": (
                "Consulta simple: un activo o comparacion directa, sin formato exigido ni varias salidas "
                "simultaneas. Suele requerir metricas esenciales y una respuesta breve."
            ),
            "structured_queries": (
                "Consulta estructurada: pide comparacion clara, tabla, serie, desglose retorno-riesgo o una "
                "explicacion mas rica. Debe reflejarse en output_requirements y presentation_preferences."
            ),
            "advanced_queries": (
                "Consulta avanzada: impone varias restricciones a la vez, exige una salida profesional o combina "
                "varias familias de metricas, tablas y datos visuales."
            ),
            "adaptation_rule": (
                "No existe una etiqueta externa de dificultad que debas devolver. Debes inferir a partir de la "
                "peticion el grado de profundidad, estructura y detalle esperados."
            ),
        },
        "required_json_schema": {
            "analytical_goal": "str",
            "analysis_type": "uno de analysis_type_catalog",
            "metrics": ["str"],
            "required_columns": ["str"],
            "data_requirements": ["str"],
            "output_requirements": ["str"],
            "presentation_preferences": ["str"],
            "reasoning": "str",
        },
    }
    return [
        LLMMessage("system", ANALYSIS_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Agente 2 - ANALISTA.\n"
            "Devuelve exclusivamente un objeto JSON valido con el esquema indicado. No incluyas markdown.\n"
            "Tu tarea es convertir la peticion del usuario y los datos ya descargados en un plan verificable para un script Python posterior. "
            "No calcules cifras y no redactes la respuesta final.\n"
            "Debes apoyarte solo en el contexto de entrada ya resuelto por la fase de datos.\n"
            "required_columns debe referirse a columnas de los datos disponibles.\n"
            "output_requirements y presentation_preferences no pueden quedar vacios: deben reflejar de forma explicita "
            "que salida estructurada devolvera el script y como debe presentarse el resultado.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]


def build_codegen_messages(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    input_payload: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    """Prompt del Agente 3: generar el script Python a partir del plan analitico."""
    current_input = input_payload or query_input.to_dict()
    payload = {
        "original_user_message": query_input.query,
        "input": current_input,
        "analysis_plan": plan.to_dict(),
        "required_json_schema": {"code": "str"},
        "code_contract": {
            "argv_1": "ruta a un JSON payload con query, tickers, csv_paths y analysis_plan",
            "stdout": "un unico JSON valido",
            "required_top_level_keys": ["metrics", "summary", "limitations"],
            "optional_top_level_keys": ["analysis_type", "tables", "series", "diagnostics"],
            "allowed_imports": [
                "json",
                "sys",
                "pathlib",
                "math",
                "statistics",
                "pandas",
                "numpy",
                "src.execution.market_data",
            ],
            "implementation_rules": [
                "Implementa solo los calculos pedidos en analysis_plan.",
                "Si faltan datos, devuelve limitations en vez de inventar resultados.",
                "No cambies tickers, fechas, intervalo ni objetivo analitico.",
                "No generes texto final para el usuario fuera del JSON.",
            ],
            "mandatory_data_loader": (
                "Usa from src.execution.market_data import load_close_prices, load_market_data, ticker_summary, make_json_safe. "
                "Para precios de cierre usa close = load_close_prices(payload['csv_paths'], payload['tickers']); "
                "close tiene indice Date y una columna por ticker. "
                "Para volumen, high o low usa data = load_market_data(payload['csv_paths'], payload['tickers']); "
                "data tiene columnas Date, Ticker, Open, High, Low, Close, Adj Close y Volume. "
                "No uses pd.read_csv directamente. "
                "Antes de imprimir, usa print(json.dumps(make_json_safe(output), ensure_ascii=False))."
            ),
            "payload_loading": "Usa json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')). No uses open().",
        },
    }
    return [
        LLMMessage("system", ANALYSIS_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Agente 3 - GENERADOR DE CODIGO.\n"
            "Devuelve exclusivamente un objeto JSON valido con un unico campo code. No incluyas markdown.\n"
            "El valor code debe ser un script Python completo, autocontenido y ejecutable.\n"
            "Debes implementar el AnalysisPlan recibido, no reinterpretar la consulta desde cero.\n"
            f"{json.dumps(payload, ensure_ascii=False)}",
        ),
    ]


def build_code_validation_messages(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    generated_code: str,
    input_payload: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    """Prompt del Agente 4: validar el codigo generado antes de ejecutarlo."""
    payload = {
        "original_user_message": query_input.query,
        "input": input_payload or query_input.to_dict(),
        "analysis_plan": plan.to_dict(),
        "generated_code": generated_code,
        "expected_code_output_contract": {
            "stdout": "un unico JSON valido",
            "required_top_level_keys": ["metrics", "summary", "limitations"],
            "optional_top_level_keys": ["analysis_type", "tables", "series", "diagnostics"],
        },
        "required_json_schema": {
            "decision": "valid | repairable | blocked",
            "errors": ["str"],
            "warnings": ["str"],
            "required_fixes": ["str"],
            "reasoning": "str",
        },
    }
    return [
        LLMMessage("system", ANALYSIS_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Agente 4 - VALIDADOR DE CODIGO.\n"
            "Tu tarea es revisar el script generado y decidir si puede pasar a ejecucion, si necesita correccion o si debe bloquearse.\n"
            "Devuelve exclusivamente JSON valido con los campos decision, errors, warnings, required_fixes y reasoning. No incluyas markdown.\n"
            "No ejecutes el codigo. No reescribas el script. No cambies el AnalysisPlan.\n"
            "Debes evaluar si el codigo implementa el plan recibido, si respeta el contexto de entrada y si mantiene una salida estructurada coherente con el workflow.\n"
            "No confundas el esquema JSON de tu propia respuesta como validador con el JSON que debe imprimir el script.\n"
            "El script debe imprimir metrics, summary y limitations, y opcionalmente analysis_type, tables, series o diagnostics.\n"
            f"{json.dumps(payload, ensure_ascii=False)}",
        ),
    ]


def build_code_repair_messages(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    previous_code: str,
    error_detail: str,
    input_payload: dict[str, Any] | None = None,
) -> list[LLMMessage]:
    """Prompt de reparacion usado por validacion y ejecucion de codigo."""
    payload = {
        "original_user_message": query_input.query,
        "input": input_payload or query_input.to_dict(),
        "analysis_plan": plan.to_dict(),
        "previous_code": previous_code,
        "error_detail": error_detail,
        "expected_code_output_contract": {
            "stdout": "un unico JSON valido",
            "required_top_level_keys": ["metrics", "summary", "limitations"],
            "optional_top_level_keys": ["analysis_type", "tables", "series", "diagnostics"],
        },
        "required_json_schema": {"code": "str"},
    }
    return [
        LLMMessage("system", ANALYSIS_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Subagente 3 - REPARACION DE CODIGO.\n"
            "El codigo anterior fallo o fue rechazado. Devuelve exclusivamente JSON valido con un unico campo code. "
            "El script corregido debe ser completo, no un parche parcial.\n"
            "No cambies el contrato de entrada ni el contrato de salida del workflow.\n"
            "El script corregido debe imprimir un JSON con metrics, summary y limitations, y opcionalmente analysis_type, tables, series o diagnostics.\n"
            f"{json.dumps(payload, ensure_ascii=False)}",
        ),
    ]


def build_interpretation_messages(output: dict, plan: AnalysisPlan) -> list[LLMMessage]:
    """Prompt del Agente 5: redactar la respuesta final sin recalcular metricas."""
    payload = {
        "execution_output": output,
        "analysis_plan": plan.to_dict(),
    }
    return [
        LLMMessage("system", ANALYSIS_SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Agente 5 - INTERPRETE.\n"
            "Redacta la respuesta final para el usuario usando unicamente execution_output y analysis_plan. "
            "No recalcules, no completes cifras ausentes y no incorpores datos externos.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]
