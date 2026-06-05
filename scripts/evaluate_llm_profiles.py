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

from src.config import RESULTS_DIR
from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


EVALUATION_DIR = RESULTS_DIR / "evaluations"
DEFAULT_MODEL_LABELS = ["openai"]
INVESTMENT_RECOMMENDATION_TERMS = {
    "compra",
    "comprar",
    "vende",
    "vender",
    "recomiendo invertir",
    "deberias invertir",
    "deberías invertir",
}


def _quality_checks(answer: str, warnings: list[str], status: str) -> dict[str, Any]:
    normalized = answer.lower()
    llm_error_markers = (
        "no se pudo",
        "falta configurar",
        "no cumple el contrato",
    )
    llm_error = status != "completed" or any(
        any(marker in warning.lower() for marker in llm_error_markers)
        for warning in warnings
    )
    forbidden_terms = sorted(term for term in INVESTMENT_RECOMMENDATION_TERMS if term in normalized)
    return {
        "completed": status == "completed",
        "llm_error": llm_error,
        "has_warnings": bool(warnings),
        "avoids_investment_recommendation": not forbidden_terms,
        "forbidden_terms": forbidden_terms,
        "answer_length_chars": len(answer),
    }


def _run_case(model_label: str, example_name: str) -> dict[str, Any]:
    started = time.perf_counter()
    workflow = build_workflow()
    state = workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS[example_name]))
    elapsed = time.perf_counter() - started
    warnings = list(state.warnings)
    return {
        "model_label": model_label,
        "example": example_name,
        "status": state.status,
        "execution_returncode": state.execution_returncode,
        "warnings": warnings,
        "final_answer": state.final_answer,
        "analysis_plan": state.analysis_plan,
        "execution_output": state.execution_output,
        "elapsed_seconds": round(elapsed, 3),
        "quality_checks": _quality_checks(state.final_answer, warnings, state.status),
    }


def _parse_examples(value: list[str]) -> list[str]:
    if value == ["all"]:
        return sorted(SAMPLE_INPUTS)
    unknown = sorted(set(value) - set(SAMPLE_INPUTS))
    if unknown:
        raise ValueError(f"Ejemplos no reconocidos: {', '.join(unknown)}")
    return value


def _write_results(payload: dict[str, Any]) -> Path:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = EVALUATION_DIR / f"llm_profile_evaluation_{timestamp}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalua el modelo OpenAI configurado sobre los ejemplos del MVP.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODEL_LABELS,
        help="Etiquetas de ejecucion para el modelo OpenAI configurado.",
    )
    parser.add_argument("--examples", nargs="+", default=["all"], help="Ejemplos concretos o 'all'.")
    parser.add_argument("--no-write", action="store_true", help="No guarda JSON en results/evaluations.")
    parser.add_argument("--show-answers", action="store_true", help="Muestra en consola la respuesta final de cada ejecucion.")
    args = parser.parse_args()

    examples = _parse_examples(args.examples)
    started_at = datetime.now().isoformat(timespec="seconds")
    results: list[dict[str, Any]] = []

    for model_label in args.models:
        for example in examples:
            result = _run_case(model_label, example)
            results.append(result)
            execution_mode = "llm/error" if result["quality_checks"]["llm_error"] else "llm/directo"
            print(
                f"{model_label:13} {example:18} {result['status']:10} "
                f"{result['elapsed_seconds']:6.2f}s {execution_mode}"
            )
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"Warning: {warning}")
            if args.show_answers:
                print(f"Respuesta final:\n{result['final_answer']}\n")

    payload = {
        "started_at": started_at,
        "models": args.models,
        "examples": examples,
        "results": results,
    }

    if not args.no_write:
        output_path = _write_results(payload)
        print(f"\nResultados guardados en: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
