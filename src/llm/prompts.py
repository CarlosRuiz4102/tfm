from __future__ import annotations

import json

from src.llm.client import LLMMessage
from src.schemas import AnalysisPlan, FinancialQueryInput


SYSTEM_PROMPT = (
    "Eres un componente profesional de analisis financiero historico asistido por LLM. "
    "Trabajas exclusivamente con datos historicos ya disponibles en CSV y con el contrato JSON indicado. "
    "No realizas predicciones, asesoramiento de inversion, recomendaciones de compra/venta, "
    "analisis fundamental externo ni incorporas informacion que no este en la entrada."
)


def build_analysis_messages(query_input: FinancialQueryInput) -> list[LLMMessage]:
    payload = {
        "input": query_input.to_dict(),
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
                "peticion el grado de profundidad, estructura y detalle esperados. Si el usuario pide tabla, "
                "serie normalizada, drawdown, medias moviles, ranking, periodos mejores/peores o bloques de "
                "salida concretos, reflejalo directamente en output_requirements y presentation_preferences."
            ),
        },
        "required_json_schema": {
            "analytical_goal": "str",
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
            "Agente 1 - PLANIFICACION ANALITICA.\n"
            "Devuelve exclusivamente un objeto JSON valido con el esquema indicado. No incluyas markdown.\n"
            "Tu tarea es convertir la peticion del usuario en un plan verificable para un script Python posterior. "
            "No calcules cifras y no redactes la respuesta final.\n"
            "Instrucciones obligatorias:\n"
            "1. Lee la consulta completa e infiere el grado de profundidad y estructura que el usuario espera.\n"
            "2. Define analytical_goal como objetivo financiero concreto, sin palabras vagas como 'analizar' sin detalle.\n"
            "3. Define analysis_type con una etiqueta breve y descriptiva, por ejemplo historical_growth, "
            "comparative_risk_return, technical_overview o structured_financial_report.\n"
            "4. Enumera metrics con nombres calculables: retorno_total, cagr, volatilidad, max_drawdown, "
            "correlacion, medias_moviles, ranking_mensual u otros si la consulta los exige.\n"
            "5. Enumera required_columns segun los calculos: Close para rentabilidad, High/Low para rangos, "
            "Volume para volumen, Open si la consulta lo requiere.\n"
            "6. Enumera data_requirements con granularidad temporal, activos, comparaciones y validaciones minimas.\n"
            "7. Enumera output_requirements con tablas, metricas y datos visuales esperados; no pidas imagenes, pide datos JSON.\n"
            "8. Enumera presentation_preferences con el tono, estructura y nivel de detalle esperado para el agente interpretador.\n"
            "9. En reasoning justifica brevemente por que la consulta requiere ese grado de profundidad y esas metricas, "
            "sin exponer cadena de pensamiento extensa.\n"
            "Restricciones: usa solo CSV, tickers y fechas de entrada; no uses noticias, fundamentales, precios actuales externos, "
            "predicciones ni recomendaciones de inversion.\n"
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
            "required_top_level_keys": ["metrics", "summary", "limitations"],
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
                "Incluye metricas suficientes para responder a la consulta segun analysis_plan. "
                "Si la consulta es simple, metrics y summary pueden bastar si no se pide formato adicional. "
                "Si hay comparacion o desglose, incluye table_data. Si se piden series o apoyo visual, incluye chart_data "
                "o visualization_data. Si la consulta exige una respuesta rica o por bloques, separa summary, metrics, "
                "table_data, chart_data/visualization_data, observations y limitations segun corresponda. "
                "Si se piden datos visuales, no generes imagenes: devuelve datos JSON con tipo sugerido, ejes, series y etiquetas. "
                "No devuelvas series largas completas: muestrea como maximo 120 puntos por serie e incluye fecha inicial/final."
            ),
        },
    }
    return [
        LLMMessage("system", SYSTEM_PROMPT),
        LLMMessage(
            "user",
            "Agente 2 - GENERACION DE CODIGO PYTHON.\n"
            "Devuelve exclusivamente un objeto JSON valido con un unico campo code. No incluyas markdown.\n"
            "El valor code debe ser un script Python completo, autocontenido y ejecutable. "
            "Debe leer el payload desde argv[1], calcular solo con los CSV indicados y escribir un unico JSON en stdout.\n"
            "Contrato tecnico obligatorio:\n"
            "1. Define main() y protege la entrada con if __name__ == '__main__'.\n"
            "2. Lee el payload con json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')). No uses open().\n"
            "3. Usa load_close_prices para precios de cierre y load_market_data para OHLCV. No uses pd.read_csv.\n"
            "4. Usa solo imports permitidos. No uses red, ficheros adicionales, subprocess, os, eval, exec ni rutas no recibidas.\n"
            "5. Devuelve siempre metrics, summary y limitations.\n"
            "6. Cuando la consulta o el plan pidan comparaciones, rankings o bloques de metricas, incluye table_data.\n"
            "7. Para peticiones visuales, incluye chart_data o visualization_data con tipo sugerido, series muestreadas, "
            "ejes y unidades; nunca generes PNG/PDF/SVG.\n"
            "8. Calcula con cuidado: ordena por fecha, elimina NaN donde proceda, evita division por cero, "
            "convierte Series a escalares antes de compararlas y controla datos insuficientes.\n"
            "9. Pasa la salida por make_json_safe antes de json.dumps.\n"
            "10. Si una metrica no puede calcularse, incluye null y una limitacion explicita; no inventes valores.\n"
            "No redactes la respuesta final al usuario: solo resultados estructurados y trazables.\n"
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
            "REPARACION DE CODIGO DEL AGENTE 2.\n"
            "El codigo anterior fallo o fue rechazado. Devuelve exclusivamente JSON valido con un unico campo code. "
            "El script corregido debe ser completo, no un parche parcial. Mantén el objetivo y las salidas "
            "solicitadas por el plan. Corrige la causa concreta indicada en error_detail y conserva el contrato: "
            "Path(sys.argv[1]).read_text, load_close_prices/load_market_data, make_json_safe, stdout con un unico JSON, "
            "sin open(), pd.read_csv, os, subprocess, eval, exec, red ni markdown.\n"
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
            "Agente 3 - INTERPRETACION FINANCIERA EN ESPANOL.\n"
            "Redacta la respuesta final para el usuario usando unicamente execution_output y analysis_plan. "
            "No recalcules, no completes cifras ausentes y no incorpores datos externos. "
            "Debes devolver texto en espanol con frases completas. No devuelvas JSON, diccionarios, listas, "
            "bloques de codigo ni una repeticion aislada de las metricas.\n"
            "Reglas de respuesta:\n"
            "1. Ajusta la extension y estructura a la complejidad de la consulta y a presentation_preferences. "
            "Si la peticion es simple, responde de forma breve y directa; si es comparativa o estructurada, "
            "organiza mejor la respuesta; si exige una salida rica o profesional, usa apartados claros.\n"
            "2. Distingue datos historicos observados, lectura interpretativa y limitaciones.\n"
            "3. Si hay tablas o datos visuales en la salida, describe que muestran sin fingir que existe una imagen.\n"
            "4. Si una metrica es null o hay datos insuficientes, indicalo como limitacion, no como error oculto.\n"
            "5. No uses tono persuasivo, no des recomendaciones de compra/venta, no predigas rendimiento futuro "
            "y no uses informacion fundamental, noticias o precios externos.\n"
            "6. Mantén español claro, profesional y comprensible para un usuario no tecnico.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]
