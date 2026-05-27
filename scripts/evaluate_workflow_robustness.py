from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import RAW_DATA_DIR, RESULTS_DIR
from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


EVALUATION_DIR = RESULTS_DIR / "evaluations"
INVESTMENT_RECOMMENDATION_TERMS = {
    "compra",
    "comprar",
    "vende",
    "vender",
    "recomiendo invertir",
    "deberias invertir",
    "deberías invertir",
}


def _raw(name: str) -> str:
    return str((RAW_DATA_DIR / name).resolve())


def _tiny_csv() -> str:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    path = EVALUATION_DIR / "stress_tiny_single_row.csv"
    path.write_text(
        "\n".join(
            [
                "Ticker,TINY,TINY,TINY,TINY,TINY,TINY",
                "Price,Open,High,Low,Close,Adj Close,Volume",
                "Date,,,,,,",
                "2026-01-02,10,10,10,10,10,1000",
            ]
        ),
        encoding="utf-8",
    )
    return str(path.resolve())


def _build_cases() -> list[dict[str, Any]]:
    tiny_csv = _tiny_csv()
    valid_cases = [
        ("base_growth_nvda", SAMPLE_INPUTS["growth_nvda"]),
        ("base_compare_nvda_amd", SAMPLE_INPUTS["compare_nvda_amd"]),
        ("base_overview_aapl", SAMPLE_INPUTS["overview_aapl"]),
        ("base_returns_qqq_spy", SAMPLE_INPUTS["returns_qqq_spy"]),
        ("base_risk_qqq_spy", SAMPLE_INPUTS["risk_qqq_spy"]),
        ("base_technical_aapl", SAMPLE_INPUTS["technical_aapl"]),
        (
            "variant_growth_btc",
            {
                "query": "Cuánto ha crecido Bitcoin en 2024",
                "intent": "price_growth",
                "tickers": ["BTC-USD"],
                "start": "2024-01-01",
                "end": "2024-12-31",
                "period": None,
                "interval": "1d",
                "csv_paths": [_raw("datos_de_bitcoin_desde_20240101_hasta_20241231.csv")],
                "warnings": [],
            },
        ),
        (
            "variant_overview_sp500",
            {
                "query": "Resume el comportamiento del S&P 500 desde 2020",
                "intent": "asset_overview",
                "tickers": ["^GSPC"],
                "start": "2020-01-01",
                "end": None,
                "period": None,
                "interval": "1d",
                "csv_paths": [_raw("descrgame_el_histrico_del_sp_500_desde_2020.csv")],
                "warnings": [],
            },
        ),
        (
            "variant_returns_btc",
            {
                "query": "Analiza los retornos de Bitcoin en 2024",
                "intent": "return_analysis",
                "tickers": ["BTC-USD"],
                "start": "2024-01-01",
                "end": "2024-12-31",
                "period": None,
                "interval": "1d",
                "csv_paths": [_raw("datos_de_bitcoin_desde_20240101_hasta_20241231.csv")],
                "warnings": [],
            },
        ),
        (
            "variant_risk_btc",
            {
                "query": "Analiza el riesgo historico de Bitcoin en 2024",
                "intent": "historical_risk_analysis",
                "tickers": ["BTC-USD"],
                "start": "2024-01-01",
                "end": "2024-12-31",
                "period": None,
                "interval": "1d",
                "csv_paths": [_raw("datos_de_bitcoin_desde_20240101_hasta_20241231.csv")],
                "warnings": [],
            },
        ),
        (
            "variant_technical_eurusd",
            {
                "query": "Haz análisis técnico de EUR/USD a 1h",
                "intent": "technical_analysis",
                "tickers": ["EURUSD=X"],
                "start": None,
                "end": None,
                "period": "10d",
                "interval": "1h",
                "csv_paths": [_raw("eurusd_en_10_das_a_1h.csv")],
                "warnings": [],
            },
        ),
        (
            "variant_technical_gold",
            {
                "query": "Haz análisis técnico del oro en 1 semana",
                "intent": "technical_analysis",
                "tickers": ["GC=F"],
                "start": None,
                "end": None,
                "period": "1wk",
                "interval": "1h",
                "csv_paths": [_raw("quiero_el_oro_en_1_semana_a_1h.csv")],
                "warnings": [],
            },
        ),
    ]

    base_growth = dict(SAMPLE_INPUTS["growth_nvda"])
    base_compare = dict(SAMPLE_INPUTS["compare_nvda_amd"])
    base_overview = dict(SAMPLE_INPUTS["overview_aapl"])
    base_technical = dict(SAMPLE_INPUTS["technical_aapl"])

    stress_cases = [
        ("stress_empty_query", {**base_growth, "query": ""}),
        ("stress_invalid_start_date", {**base_growth, "start": "17/03/2021"}),
        ("stress_invalid_end_date", {**base_growth, "end": "16-03-2026"}),
        ("stress_missing_csv", {**base_growth, "csv_paths": [_raw("missing_file.csv")]}),
        ("stress_no_ticker", {**base_growth, "tickers": []}),
        ("stress_no_csv", {**base_growth, "csv_paths": []}),
        ("stress_unknown_ticker_in_csv", {**base_overview, "tickers": ["MSFT"]}),
        (
            "stress_returns_insufficient_data",
            {
                "query": "Analiza retornos con una sola fila",
                "intent": "return_analysis",
                "tickers": ["TINY"],
                "start": None,
                "end": None,
                "period": None,
                "interval": "1d",
                "csv_paths": [tiny_csv],
                "warnings": [],
            },
        ),
        (
            "stress_technical_insufficient_data",
            {
                "query": "Analiza técnico con una sola fila",
                "intent": "technical_analysis",
                "tickers": ["TINY"],
                "start": None,
                "end": None,
                "period": None,
                "interval": "1d",
                "csv_paths": [tiny_csv],
                "warnings": [],
            },
        ),
    ]

    cases: list[dict[str, Any]] = []
    for name, payload in valid_cases:
        cases.append({"name": name, "group": "functional", "expected_status": "completed", "payload": payload})
    for name, payload in stress_cases:
        cases.append({"name": name, "group": "stress", "expected_status": "completed_with_error", "payload": payload})
    return cases


def _quality_checks(state_status: str, final_answer: str, warnings: list[str], expected_status: str) -> dict[str, Any]:
    normalized_answer = final_answer.lower()
    forbidden_terms = sorted(term for term in INVESTMENT_RECOMMENDATION_TERMS if term in normalized_answer)
    return {
        "expected_status_met": state_status == expected_status,
        "avoids_investment_recommendation": not forbidden_terms,
        "forbidden_terms": forbidden_terms,
        "has_warnings": bool(warnings),
        "answer_length_chars": len(final_answer),
    }


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    workflow = build_workflow()
    started = time.perf_counter()
    state = workflow.invoke(FinancialQueryInput.from_dict(case["payload"]))
    elapsed = time.perf_counter() - started
    warnings = list(state.warnings)
    return {
        "name": case["name"],
        "group": case["group"],
        "input_intent_hint": case["payload"].get("intent"),
        "expected_status": case["expected_status"],
        "status": state.status,
        "execution_returncode": state.execution_returncode,
        "elapsed_seconds": round(elapsed, 3),
        "warnings": warnings,
        "error_message": state.error_message,
        "final_answer": state.final_answer,
        "analysis_plan": state.analysis_plan,
        "execution_output": state.execution_output,
        "quality_checks": _quality_checks(state.status, state.final_answer, warnings, case["expected_status"]),
    }


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    functional = [item for item in results if item["group"] == "functional"]
    stress = [item for item in results if item["group"] == "stress"]
    expected_met = [item for item in results if item["quality_checks"]["expected_status_met"]]
    completed = [item for item in results if item["status"] == "completed"]
    controlled_errors = [item for item in results if item["status"] == "completed_with_error"]
    return {
        "total_cases": total,
        "functional_cases": len(functional),
        "stress_cases": len(stress),
        "expected_status_met": len(expected_met),
        "expected_status_rate": round(len(expected_met) / total, 4) if total else 0.0,
        "functional_success": sum(item["status"] == "completed" for item in functional),
        "stress_controlled_errors": sum(item["status"] == "completed_with_error" for item in stress),
        "warnings": sum(len(item["warnings"]) for item in results),
        "investment_recommendation_violations": sum(
            not item["quality_checks"]["avoids_investment_recommendation"] for item in results
        ),
        "avg_elapsed_seconds_all": round(mean(item["elapsed_seconds"] for item in results), 3) if results else 0.0,
        "avg_elapsed_seconds_functional": round(mean(item["elapsed_seconds"] for item in functional), 3) if functional else 0.0,
        "avg_elapsed_seconds_stress": round(mean(item["elapsed_seconds"] for item in stress), 3) if stress else 0.0,
        "completed_cases": len(completed),
        "controlled_error_cases": len(controlled_errors),
    }


def main() -> int:
    cases = _build_cases()
    results = [_run_case(case) for case in cases]
    aggregate = _aggregate(results)
    payload = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "llm",
        "aggregate": aggregate,
        "results": results,
    }
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVALUATION_DIR / f"workflow_robustness_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    print(f"Resultados guardados en: {output_path}")
    for item in results:
        marker = "OK" if item["quality_checks"]["expected_status_met"] else "FAIL"
        print(
            f"{marker:4} {item['group']:10} {item['name']:36} "
            f"{item['status']:20} {item['elapsed_seconds']:6.3f}s"
        )
    return 0 if aggregate["expected_status_met"] == aggregate["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
