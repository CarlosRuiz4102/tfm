from __future__ import annotations

import json

from src.llm.client import LLMMessage
from src.schemas import AnalysisPlan, FinancialQueryInput


SYSTEM_PROMPT = (
    "Eres un modulo LLM analitico financiero dentro de un TFM. "
    "Trabajas solo con datos historicos ya cargados en CSV. "
    "No haces prediccion futura, recomendacion de inversion ni analisis fundamental complejo."
)


def build_analysis_messages(query_input: FinancialQueryInput) -> list[LLMMessage]:
    payload = {
        "input": query_input.to_dict(),
        "quality_guidelines": {
            "level_a": (
                "Consulta simple sin formato especial: respuesta breve y metricas basicas. "
                "No fuerces graficas si no aportan valor o no se piden."
            ),
            "level_b": (
                "Analisis mas completo o comparativa clara: metricas en tabla/bloque estructurado "
                "y una grafica principal o datos para representarla."
            ),
            "level_c": (
                "Analisis profesional, detallado o con varias salidas concretas: varias metricas, "
                "tablas y visualizaciones/datos visuales segun la peticion."
            ),
            "adaptation_rule": (
                "Si el usuario pide explicitamente una tabla, grafica normalizada, drawdown, "
                "medias moviles u otra salida, incluyelo en output_requirements aunque la consulta sea simple."
            ),
        },
        "required_json_schema": {
            "interpreted_intent": "str",
            "analysis_type": "str",
            "metrics": ["str"],
            "required_columns": ["str"],
            "data_requirements": ["str"],
            "output_requirements": ["str"],
            "presentation_preferences": ["str"],
            "reasoning": "str",
        },
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Devuelve solo JSON valido. Interpreta la intencionalidad de la consulta, "
            "decide que analisis financiero hace falta y describe que debe calcular el script. "
            "Clasifica implicitamente la profundidad como Nivel A, B o C dentro de "
            "presentation_preferences y output_requirements. "
            "Nivel A: query simple, metricas basicas y respuesta breve. "
            "Nivel B: analisis mas completo con tabla y una grafica principal o datos para generarla. "
            "Nivel C: analisis profesional/detallado con varias tablas o visualizaciones si se piden. "
            "No inventes datos externos: usa solo los CSV, tickers y fechas de la entrada.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]


def build_codegen_messages(query_input: FinancialQueryInput, plan: AnalysisPlan) -> list[LLMMessage]:
    payload = {
        "original_user_message": query_input.query,
        "input": query_input.to_dict(),
        "analysis_plan": plan.to_dict(),
        "required_json_schema": {"code": "str"},
        "code_contract": {
            "argv_1": "ruta a un JSON payload con query, tickers, csv_paths y analysis_plan",
            "stdout": "un unico JSON valido",
            "required_top_level_keys": ["analysis_type", "metrics", "summary"],
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
            "presentation_contract": (
                "Incluye en el JSON metricas suficientes para el nivel pedido. "
                "Si el usuario pide tabla, devuelve datos tabulares como listas/dicts. "
                "Si pide grafica, no generes imagenes: devuelve chart_data o visualization_data "
                "con series, etiquetas y tipo sugerido. "
                "No devuelvas series completas si son largas: muestrea como maximo 120 puntos por serie "
                "e incluye resumen, fecha inicial y fecha final."
            ),
        },
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Devuelve solo JSON valido con un campo code. "
            "El codigo debe ser Python ejecutable, leer el payload recibido por argv[1] y escribir JSON en stdout. "
            "No redactes la respuesta final al usuario: calcula metricas y devuelve resultados estructurados. "
            "Adapta la salida al nivel de analisis pedido: A metricas basicas, B tabla y una visualizacion/datos visuales, "
            "C varias metricas/tablas/visualizaciones segun la consulta. "
            "Si se solicita una grafica, representa sus datos en JSON como chart_data o visualization_data; "
            "no crees ficheros de imagen y limita cada serie visual a un maximo de 120 puntos muestreados. "
            "Incluye una funcion main() y usa solo imports permitidos. "
            "IMPORTANTE: para leer el JSON de entrada usa Path(sys.argv[1]).read_text; no uses open(). "
            "IMPORTANTE: para cierres usa load_close_prices; para OHLCV usa load_market_data. "
            "No uses pd.read_csv porque los CSV tienen cabeceras yfinance. "
            "Convierte Series de pandas a escalares antes de compararlas: usa float(serie.iloc[0]) o selecciona una columna. "
            "Antes de json.dumps, pasa el resultado por make_json_safe para convertir numpy, pandas y fechas. "
            "Manten el codigo compacto y devuelve JSON estricto, sin markdown.\n"
            f"{json.dumps(payload, ensure_ascii=False)}",
        ),
    ]


def build_code_repair_messages(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    previous_code: str,
    error_detail: str,
) -> list[LLMMessage]:
    payload = {
        "original_user_message": query_input.query,
        "input": query_input.to_dict(),
        "analysis_plan": plan.to_dict(),
        "previous_code": previous_code,
        "error_detail": error_detail,
        "required_json_schema": {"code": "str"},
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "El codigo generado fallo o fue rechazado. Devuelve solo JSON valido con un campo code "
            "que contenga una version corregida completa del script Python. "
            "Manten el objetivo analitico original, incluido el nivel A/B/C y las salidas tabulares o visuales pedidas. "
            "Usa Path(sys.argv[1]).read_text para el payload. "
            "Usa load_close_prices para cierres y load_market_data para OHLCV. "
            "Antes de json.dumps, usa make_json_safe. No uses open(), pd.read_csv, os ni subprocess. "
            "No incluyas markdown ni explicaciones.\n"
            f"{json.dumps(payload, ensure_ascii=False)}",
        ),
    ]


def build_interpretation_messages(output: dict, plan: AnalysisPlan) -> list[LLMMessage]:
    payload = {
        "execution_output": output,
        "analysis_plan": plan.to_dict(),
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Redacta una respuesta breve en espanol para usuario final. "
            "Interpreta las metricas recibidas y explica que significan en lenguaje claro. "
            "Adapta la profundidad al plan: si el analisis es simple, se conciso; si el plan pide "
            "tabla, grafica o analisis profesional, organiza la respuesta alrededor de esos resultados. "
            "Distingue datos historicos observados, interpretacion y limitaciones. "
            "Respeta las metricas recibidas, no anadas datos externos, no hagas predicciones "
            "y evita recomendaciones de inversion.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]
