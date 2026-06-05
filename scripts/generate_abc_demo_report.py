from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import LLMConfig, RAW_DATA_DIR, RESULTS_DIR
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


REPORT_PATH = RESULTS_DIR / "reports" / "salidas_ejecucion_bateria_abc.md"


def _raw(name: str) -> str:
    return str((RAW_DATA_DIR / name).resolve())


DEMO_CASES: list[dict[str, Any]] = [
    {
        "id": "level_a_nvda_growth",
        "level": "A",
        "expected_depth": "A1: crecimiento simple con precio inicial/final y retorno acumulado.",
        "input": {
            "query": "Cuanto ha crecido Nvidia en los ultimos 5 anos",
            "tickers": ["NVDA"],
            "period": "5y",
            "interval": "1d",
            "csv_paths": [_raw("cunto_ha_crecido_nvidia_en_5_aos.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_a_nvda_amd_compare",
        "level": "A",
        "expected_depth": "A2: comparacion simple con rentabilidad acumulada por activo.",
        "input": {
            "query": "Compara Nvidia y AMD en 2 anos",
            "tickers": ["NVDA", "AMD"],
            "period": "2y",
            "interval": "1d",
            "csv_paths": [_raw("compara_nvidia_y_amd_en_2_aos.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_a_aapl_overview",
        "level": "A",
        "expected_depth": "A3: vision descriptiva breve con rango de precios y tendencia observada.",
        "input": {
            "query": "Dame una vision general de AAPL en 3 meses",
            "tickers": ["AAPL"],
            "period": "3mo",
            "interval": "1d",
            "csv_paths": [_raw("aapl_en_3_meses.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_a_qqq_spy_returns",
        "level": "A",
        "expected_depth": "A4: retornos historicos resumidos para dos activos.",
        "input": {
            "query": "Analiza los retornos de QQQ y SPY en 2024",
            "tickers": ["QQQ", "SPY"],
            "start": "2024-01-01",
            "end": "2024-12-31",
            "interval": "1d",
            "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_a_qqq_spy_risk",
        "level": "A",
        "expected_depth": "A5: riesgo historico basico con volatilidad, mejor/peor dia y drawdown.",
        "input": {
            "query": "Analiza el riesgo historico de QQQ y SPY en 2024",
            "tickers": ["QQQ", "SPY"],
            "start": "2024-01-01",
            "end": "2024-12-31",
            "interval": "1d",
            "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_b_nvda_complete",
        "level": "B",
        "expected_depth": "B1: analisis ampliado de un activo con tabla y datos de evolucion.",
        "input": {
            "query": "Hazme un analisis mas completo de Nvidia en los ultimos 5 anos con tabla y una serie de evolucion",
            "tickers": ["NVDA"],
            "period": "5y",
            "interval": "1d",
            "csv_paths": [_raw("cunto_ha_crecido_nvidia_en_5_aos.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_b_qqq_spy_clear_compare",
        "level": "B",
        "expected_depth": "B2: comparativa con tabla y serie normalizada base 100.",
        "input": {
            "query": "Comparame QQQ y SPY en 2024 de forma clara, con tabla y serie normalizada",
            "tickers": ["QQQ", "SPY"],
            "start": "2024-01-01",
            "end": "2024-12-31",
            "interval": "1d",
            "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_b_aapl_risk_return",
        "level": "B",
        "expected_depth": "B3: retorno-riesgo con explicacion didactica y metricas estructuradas.",
        "input": {
            "query": "Quiero entender retorno y riesgo de AAPL en 3 meses con una explicacion sencilla",
            "tickers": ["AAPL"],
            "period": "3mo",
            "interval": "1d",
            "csv_paths": [_raw("aapl_en_3_meses.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_b_btc_2024_profile",
        "level": "B",
        "expected_depth": "B4: perfil de activo volatil con rentabilidad, volatilidad y drawdown.",
        "input": {
            "query": (
                "Analiza Bitcoin durante 2024 con una tabla de rentabilidad, volatilidad, maximo drawdown, "
                "maximo y minimo, y datos para una serie de evolucion"
            ),
            "tickers": ["BTC-USD"],
            "start": "2024-01-01",
            "end": "2024-12-31",
            "interval": "1d",
            "csv_paths": [_raw("datos_de_bitcoin_desde_20240101_hasta_20241231.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_b_eurusd_intraday",
        "level": "B",
        "expected_depth": "B5: analisis intradia con rango, volatilidad horaria y serie de evolucion.",
        "input": {
            "query": (
                "Resume el comportamiento intradia de EUR/USD durante los ultimos 10 dias con datos horarios. "
                "Incluye tabla de variacion, rango medio, volatilidad horaria y datos para una serie de evolucion"
            ),
            "tickers": ["EURUSD=X"],
            "period": "10d",
            "interval": "1h",
            "csv_paths": [_raw("eurusd_en_10_das_a_1h.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_c_qqq_spy_professional",
        "level": "C",
        "expected_depth": "C1: informe comparativo con tabla, normalizacion, drawdown y limitaciones.",
        "input": {
            "query": (
                "Haz un analisis profesional de QQQ y SPY en 2024 con tabla, serie normalizada, "
                "drawdown y conclusion para usuario no tecnico"
            ),
            "tickers": ["QQQ", "SPY"],
            "start": "2024-01-01",
            "end": "2024-12-31",
            "interval": "1d",
            "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_c_nvda_amd_multicriteria",
        "level": "C",
        "expected_depth": "C2: ranking multicriterio con rentabilidad, riesgo, drawdown y lectura separada.",
        "input": {
            "query": (
                "Compara NVDA y AMD en 2 anos con ranking por rentabilidad, riesgo y drawdown, "
                "y separa metricas, datos estructurados y limitaciones"
            ),
            "tickers": ["NVDA", "AMD"],
            "period": "2y",
            "interval": "1d",
            "csv_paths": [_raw("compara_nvidia_y_amd_en_2_aos.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_c_sp500_report",
        "level": "C",
        "expected_depth": "C3: informe de indice amplio con resumen ejecutivo, extremos y drawdown.",
        "input": {
            "query": (
                "Prepara un informe detallado del S&P 500 desde 2020 con crecimiento, volatilidad, "
                "maximo drawdown, mejores y peores periodos, y resumen ejecutivo"
            ),
            "tickers": ["^GSPC"],
            "start": "2020-01-01",
            "interval": "1d",
            "csv_paths": [_raw("descrgame_el_histrico_del_sp_500_desde_2020.csv")],
            "warnings": [],
        },
    },
    {
        "id": "level_c_gold_intraday_report",
        "level": "C",
        "expected_depth": "C4: informe intradia con mejores/peores intervalos, volumen y limitaciones.",
        "input": {
            "query": (
                "Prepara un informe detallado del oro durante la ultima semana con datos horarios. "
                "Separa metricas, tabla de mejores y peores intervalos, datos para una serie de evolucion, "
                "volatilidad horaria, rango maximo-minimo y limitaciones del analisis"
            ),
            "tickers": ["GC=F"],
            "period": "1wk",
            "interval": "1h",
            "csv_paths": [_raw("quiero_el_oro_en_1_semana_a_1h.csv")],
            "warnings": [],
        },
    },
    {
        "id": "stress_visual_qqq_spy_monthly",
        "level": "C",
        "expected_depth": (
            "C5: query de estres con formato impuesto: tabla resumen, ranking mensual, "
            "serie normalizada y serie de drawdown."
        ),
        "input": {
            "query": (
                "Compara QQQ y SPY durante 2024 como si fuera un informe para un cliente no tecnico. "
                "Quiero que me muestres los datos exactamente en cuatro bloques: "
                "1) una tabla resumen con rentabilidad total, volatilidad anualizada, maximo drawdown, "
                "mejor mes y peor mes; "
                "2) una tabla ranking mensual indicando que activo gano cada mes; "
                "3) datos para una serie normalizada base 100 de ambos activos; "
                "4) datos para una serie de drawdown. "
                "Cierra con una conclusion clara, sin recomendar comprar ni vender."
            ),
            "tickers": ["QQQ", "SPY"],
            "start": "2024-01-01",
            "end": "2024-12-31",
            "interval": "1d",
            "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
            "warnings": [],
        },
    },
]


def _json_block(value: Any, max_chars: int = 5000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [salida truncada en el informe]"
    return text


def _final_answer_block(answer: str) -> str:
    return answer.strip() or "Sin respuesta final."


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    workflow = build_workflow()
    started = time.perf_counter()
    state = workflow.invoke(FinancialQueryInput.from_dict(case["input"]))
    elapsed = time.perf_counter() - started
    return {
        "id": case["id"],
        "level": case["level"],
        "expected_depth": case["expected_depth"],
        "query": case["input"]["query"],
        "tickers": case["input"]["tickers"],
        "status": state.status,
        "elapsed_seconds": round(elapsed, 2),
        "analysis_plan": state.analysis_plan,
        "execution_output": state.execution_output,
        "final_answer": state.final_answer,
        "warnings": state.warnings,
        "error_message": state.error_message,
        "artifacts": state.execution_artifacts,
    }


def _write_report(results: list[dict[str, Any]], output_path: Path) -> None:
    config = LLMConfig.from_env()
    completed = sum(1 for item in results if item["status"] == "completed")
    lines = [
        "# Salidas de ejecucion de la bateria A/B/C",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Este informe muestra ejecuciones reales del workflow LLM + codegen + ejecucion controlada + interpretacion final.",
        "Para cada query se incluye el plan del primer agente, la salida estructurada del codigo y la respuesta que veria el cliente.",
        "",
        "## Configuracion",
        "",
        f"- Perfil LLM: `{config.profile or 'sin perfil'}`",
        f"- Modelo: `{config.model or 'sin modelo'}`",
        f"- Casos completados: `{completed}/{len(results)}`",
        "",
        "## Resumen",
        "",
        "| ID | Nivel | Estado | Tiempo |",
        "|---|---:|---:|---:|",
    ]
    for item in results:
        lines.append(f"| `{item['id']}` | {item['level']} | `{item['status']}` | {item['elapsed_seconds']} s |")

    for item in results:
        lines.extend(
            [
                "",
                f"## {item['id']} - Nivel {item['level']}",
                "",
                f"**Consulta:** {item['query']}",
                "",
                f"**Objetivo del nivel:** {item['expected_depth']}",
                "",
                f"**Estado tecnico:** `{item['status']}` en {item['elapsed_seconds']} s.",
                "",
                "### Lo que planifica el primer agente",
                "",
                "```json",
                _json_block(item["analysis_plan"]),
                "```",
                "",
                "### Salida estructurada del codigo ejecutado",
                "",
                "```json",
                _json_block(item["execution_output"]),
                "```",
                "",
                "### Lo que veriamos como cliente",
                "",
                _final_answer_block(item["final_answer"]),
            ]
        )
        if item["warnings"]:
            lines.extend(["", "### Avisos", "", "```json", _json_block(item["warnings"]), "```"])
        if item["error_message"]:
            lines.extend(["", "### Error", "", item["error_message"]])
        if item["artifacts"]:
            lines.extend(["", "### Artefactos", "", "```json", _json_block(item["artifacts"], max_chars=2000), "```"])

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera informe Markdown con salidas A/B/C ejecutadas.")
    parser.add_argument("--output", default=str(REPORT_PATH), help="Ruta del informe Markdown.")
    parser.add_argument("--cases", nargs="*", help="IDs concretos a ejecutar. Por defecto ejecuta todos.")
    args = parser.parse_args()

    selected = DEMO_CASES
    if args.cases:
        wanted = set(args.cases)
        selected = [case for case in DEMO_CASES if case["id"] in wanted]
        missing = wanted - {case["id"] for case in selected}
        if missing:
            raise ValueError(f"Casos no reconocidos: {', '.join(sorted(missing))}")

    results = []
    for case in selected:
        print(f"Ejecutando {case['id']} (Nivel {case['level']})...", flush=True)
        results.append(_run_case(case))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_report(results, output_path)
    print(f"Informe escrito en: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
