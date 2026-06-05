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
            "level_a": (
                "Nivel A: consulta directa, un activo o comparacion simple, sin formato exigido. "
                "Debe producir metricas esenciales y una respuesta breve. Ejemplos: crecimiento total, "
                "precio inicial/final, rentabilidad acumulada, volatilidad basica o resumen descriptivo."
            ),
            "level_b": (
                "Nivel B: consulta que pide mayor explicacion, comparativa clara, tabla o serie estructurada "
                "o desglose retorno-riesgo. Debe producir varias metricas, datos tabulares y como maximo "
                "datos estructurados adicionales."
            ),
            "level_c": (
                "Nivel C: consulta profesional, multicriterio o con formato impuesto. Debe coordinar "
                "varias familias de metricas, tablas y datos visuales si se solicitan, separando rendimiento, "
                "riesgo, comparacion temporal y limitaciones."
            ),
            "adaptation_rule": (
                "El nivel se decide por la peticion, no por una etiqueta externa. Si el usuario pide tabla, "
                "serie normalizada, drawdown, medias moviles, ranking, periodos mejores/peores o bloques "
                "de salida concretos, reflejalo en output_requirements y eleva el nivel si corresponde."
            ),
        },
        "required_json_schema": {
            "analysis_level": "A|B|C",
            "analytical_goal": "str",
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
            "1. Lee la consulta completa y clasifica analysis_level como A, B o C usando las reglas del payload.\n"
            "2. Define analytical_goal como objetivo financiero concreto, sin palabras vagas como 'analizar' sin detalle.\n"
            "3. Enumera metrics con nombres calculables: retorno_total, cagr, volatilidad, max_drawdown, "
            "correlacion, medias_moviles, ranking_mensual u otros si la consulta los exige.\n"
            "4. Enumera required_columns segun los calculos: Close para rentabilidad, High/Low para rangos, "
            "Volume para volumen, Open si la consulta lo requiere.\n"
            "5. Enumera data_requirements con granularidad temporal, activos, comparaciones y validaciones minimas.\n"
            "6. Enumera output_requirements con tablas, metricas y datos visuales esperados; no pidas imagenes, pide datos JSON.\n"
            "7. Enumera presentation_preferences con el tono y estructura esperada para el agente interpretador.\n"
            "8. En reasoning justifica brevemente el nivel elegido y las metricas, sin exponer cadena de pensamiento extensa.\n"
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
            "required_top_level_keys": ["analysis_level", "metrics", "summary", "limitations"],
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
                "Incluye metricas suficientes para el nivel pedido. "
                "Nivel A: metrics y summary bastan si la consulta no pide formato. "
                "Nivel B: incluye table_data cuando haya comparacion o desglose, y chart_data si se piden series estructuradas. "
                "Nivel C: separa summary, metrics, table_data, chart_data/visualization_data, observations y limitations. "
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
            "5. Devuelve siempre analysis_level, metrics, summary y limitations.\n"
            "6. Para Nivel B o C, incluye table_data cuando haya comparaciones, rankings o bloques de metricas.\n"
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
            "El script corregido debe ser completo, no un parche parcial. Mantén el objetivo, nivel A/B/C y salidas "
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
            "1. Ajusta la extension al analysis_level: A breve y directo; B estructurado con metricas principales; "
            "C informe compacto con apartados claros.\n"
            "2. Distingue datos historicos observados, lectura interpretativa y limitaciones.\n"
            "3. Si hay tablas o datos visuales en la salida, describe que muestran sin fingir que existe una imagen.\n"
            "4. Si una metrica es null o hay datos insuficientes, indicalo como limitacion, no como error oculto.\n"
            "5. No uses tono persuasivo, no des recomendaciones de compra/venta, no predigas rendimiento futuro "
            "y no uses informacion fundamental, noticias o precios externos.\n"
            "6. Mantén español claro, profesional y comprensible para un usuario no tecnico.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}",
        ),
    ]
