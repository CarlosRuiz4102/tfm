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

from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


CATALOG_PATH = ROOT / "data" / "catalog" / "bateria_50_ejemplos_v2.json"
RESULTS_DIR = ROOT / "results" / "evaluations"
RESULTS_JSON_PATH = RESULTS_DIR / "bateria_50_ejemplos_v2_results.json"
REPORT_MD_PATH = ROOT / "docs" / "evaluacion_bateria_50_ejemplos_v2.md"

LEVEL_SIZES = {"A": 10, "B": 20, "C": 20}

MOJIBAKE_REPLACEMENTS = {
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã": "Á",
    "Ã‰": "É",
    "Ã": "Í",
    "Ã“": "Ó",
    "Ãš": "Ú",
    "Ã±": "ñ",
    "Ã‘": "Ñ",
    "Ã¼": "ü",
    "â€¯": " ",
    "â€‘": "-",
    "â€“": "-",
    "â€”": "-",
    "â€œ": "\"",
    "â€": "\"",
    "â€˜": "'",
    "â€™": "'",
    "â€¦": "...",
    "âš ï¸": "AVISO:",
}


def make_case_id(index_zero_based: int) -> tuple[str, str]:
    position = index_zero_based + 1
    if position <= 10:
        return f"A{position:02d}", "A"
    if position <= 30:
        return f"B{position - 10:02d}", "B"
    return f"C{position - 30:02d}", "C"


def load_catalog() -> list[dict[str, Any]]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def load_results() -> dict[str, Any]:
    if RESULTS_JSON_PATH.exists():
        results = json.loads(RESULTS_JSON_PATH.read_text(encoding="utf-8"))
        sanitize_results(results)
        return results
    return {
        "generated_at": None,
        "catalog_path": str(CATALOG_PATH),
        "cases": {},
    }


def save_results(results: dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results["generated_at"] = datetime.now().isoformat(timespec="seconds")
    RESULTS_JSON_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\r\n", "\n").replace("\r", "\n")


def repair_text(text: str) -> str:
    repaired = text
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        repaired = repaired.replace(bad, good)
    return repaired


def sanitize_results(results: dict[str, Any]) -> None:
    for case_data in results.get("cases", {}).values():
        case_data["query"] = repair_text(case_data.get("query", ""))
        case_data["final_answer"] = repair_text(case_data.get("final_answer", ""))
        case_data["error_message"] = repair_text(case_data.get("error_message", ""))


def format_seconds(seconds: float | None) -> str:
    if seconds is None:
        return ""
    return f"{seconds:.2f} s"


def summarize_counts(cases: list[dict[str, Any]], stored_results: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total_executed": 0,
        "total_completed": 0,
        "total_error": 0,
        "total_seconds": 0.0,
        "by_level": {
            "A": {"executed": 0, "completed": 0, "error": 0, "seconds": 0.0},
            "B": {"executed": 0, "completed": 0, "error": 0, "seconds": 0.0},
            "C": {"executed": 0, "completed": 0, "error": 0, "seconds": 0.0},
        },
    }
    for idx, case in enumerate(cases):
        case_id, level = make_case_id(idx)
        case_result = stored_results["cases"].get(case_id)
        if not case_result:
            continue
        summary["total_executed"] += 1
        elapsed = case_result.get("elapsed_seconds") or 0.0
        summary["total_seconds"] += elapsed
        level_bucket = summary["by_level"][level]
        level_bucket["executed"] += 1
        level_bucket["seconds"] += elapsed
        if case_result.get("status") == "completed":
            summary["total_completed"] += 1
            level_bucket["completed"] += 1
        else:
            summary["total_error"] += 1
            level_bucket["error"] += 1
    return summary


def render_report(cases: list[dict[str, Any]], stored_results: dict[str, Any]) -> str:
    summary = summarize_counts(cases, stored_results)
    total_executed = summary["total_executed"]
    total_seconds = summary["total_seconds"]
    average_seconds = total_seconds / total_executed if total_executed else None

    lines: list[str] = []
    lines.append("# Evaluacion de bateria de 50 ejemplos v2")
    lines.append("")
    lines.append("Catalogo fuente:")
    lines.append("[bateria_50_ejemplos_v2.json](/C:/Users/usuario/Desktop/tfm/data/catalog/bateria_50_ejemplos_v2.json)")
    lines.append("")
    lines.append("Este documento se actualiza a medida que se ejecuta la bateria. La entrada del workflow en todos los casos es solo la `query`.")
    lines.append("")
    lines.append("## Resumen de ejecucion")
    lines.append("")
    lines.append(f"- Fecha de ultima actualizacion: {stored_results.get('generated_at') or ''}")
    lines.append("- Modelo configurado:")
    lines.append("- Catalogo usado: `data/catalog/bateria_50_ejemplos_v2.json`")
    lines.append(f"- Casos seleccionados: {len(cases)}")
    lines.append(f"- Casos ejecutados: {total_executed}")
    lines.append(f"- Casos completados: {summary['total_completed']}")
    lines.append(f"- Casos con error: {summary['total_error']}")
    lines.append(f"- Tiempo total observado: {format_seconds(total_seconds if total_executed else None)}")
    lines.append(f"- Tiempo medio por caso: {format_seconds(average_seconds)}")
    lines.append("- Observaciones generales:")
    lines.append("")
    lines.append("## Resumen por niveles")
    lines.append("")
    lines.append("| Nivel | Casos | Ejecutados | Completados | Con error | Tiempo total |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for level, count in LEVEL_SIZES.items():
        bucket = summary["by_level"][level]
        lines.append(
            f"| {level} | {count} | {bucket['executed']} | {bucket['completed']} | {bucket['error']} | {format_seconds(bucket['seconds'] if bucket['executed'] else None)} |"
        )
    lines.append(
        f"| Total | {len(cases)} | {total_executed} | {summary['total_completed']} | {summary['total_error']} | {format_seconds(total_seconds if total_executed else None)} |"
    )
    lines.append("")
    lines.append("## Matriz rapida")
    lines.append("")
    lines.append("| ID | Nivel | Estado | Tiempo | Query |")
    lines.append("|---|---|---|---:|---|")
    for idx, case in enumerate(cases):
        case_id, level = make_case_id(idx)
        case_result = stored_results["cases"].get(case_id, {})
        status = case_result.get("status", "")
        elapsed = format_seconds(case_result.get("elapsed_seconds"))
        query = markdown_escape(case["query"])
        lines.append(f"| {case_id} | {level} | {status} | {elapsed} | {query} |")

    lines.append("")
    lines.append("## Detalle por ejemplo")
    lines.append("")

    for idx, case in enumerate(cases):
        case_id, level = make_case_id(idx)
        case_result = stored_results["cases"].get(case_id, {})
        status = case_result.get("status", "")
        elapsed = format_seconds(case_result.get("elapsed_seconds"))
        final_answer = case_result.get("final_answer", "")
        error_message = case_result.get("error_message", "")

        lines.append(f"### {case_id} - Nivel {level}")
        lines.append("")
        lines.append(f"- Query: `{case['query']}`")
        lines.append(f"- Estado: {status}")
        lines.append(f"- Tiempo: {elapsed}")
        lines.append("- Respuesta final o error:")
        lines.append("")

        if status == "completed" and final_answer:
            lines.append("```text")
            lines.append(repair_text(final_answer).rstrip())
            lines.append("```")
        elif error_message:
            lines.append("```text")
            lines.append(repair_text(error_message).rstrip())
            lines.append("```")
        else:
            lines.append("")

        lines.append("")
        lines.append("| Criterio | Valor |")
        lines.append("|---|---|")
        lines.append("| Adecuacion a la consulta |  |")
        lines.append("| Cobertura analitica |  |")
        lines.append("| Coherencia y solidez aparente |  |")
        lines.append("| Claridad y utilidad comunicativa |  |")
        lines.append("| Prudencia y tratamiento de limitaciones |  |")
        lines.append("| Total / 10 |  |")
        lines.append("")
        lines.append("- Comentario humano:")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_report(cases: list[dict[str, Any]], stored_results: dict[str, Any]) -> None:
    REPORT_MD_PATH.write_text(render_report(cases, stored_results), encoding="utf-8")


def execute_case(workflow: Any, case_id: str, level: str, query: str) -> dict[str, Any]:
    started = time.perf_counter()
    started_at = datetime.now().isoformat(timespec="seconds")
    state = workflow.invoke(FinancialQueryInput(query=query))
    elapsed_seconds = time.perf_counter() - started
    finished_at = datetime.now().isoformat(timespec="seconds")

    status = state.status
    final_answer = state.final_answer.strip()
    error_message = ""
    if status != "completed":
        error_message = (state.error_message or state.final_answer or "Error no especificado.").strip()

    return {
        "id": case_id,
        "level": level,
        "query": repair_text(query),
        "status": status,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "final_answer": repair_text(final_answer),
        "error_message": repair_text(error_message),
        "run_id": state.run_id,
        "trace_dir": state.trace_dir,
        "started_at": started_at,
        "finished_at": finished_at,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta y documenta la bateria v2.")
    parser.add_argument("--start", type=int, default=1, help="Indice 1-based del primer caso a ejecutar.")
    parser.add_argument("--count", type=int, default=5, help="Numero de casos consecutivos a ejecutar.")
    parser.add_argument("--rewrite-report-only", action="store_true", help="Reescribe el markdown a partir del JSON de resultados sin ejecutar casos.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_catalog()
    stored_results = load_results()

    if args.rewrite_report_only:
        sanitize_results(stored_results)
        save_results(stored_results)
        write_report(cases, stored_results)
        return 0

    start_index = max(args.start - 1, 0)
    end_index = min(start_index + max(args.count, 0), len(cases))
    selected_cases = cases[start_index:end_index]

    if not selected_cases:
        raise ValueError("No hay casos seleccionados con los parametros indicados.")

    workflow = build_workflow()

    for absolute_index, case in enumerate(selected_cases, start=start_index):
        case_id, level = make_case_id(absolute_index)
        result = execute_case(workflow, case_id, level, case["query"])
        stored_results["cases"][case_id] = result
        save_results(stored_results)
        write_report(cases, stored_results)
        print(
            json.dumps(
                {
                    "id": case_id,
                    "level": level,
                    "status": result["status"],
                    "elapsed_seconds": result["elapsed_seconds"],
                    "query": case["query"],
                },
                ensure_ascii=False,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
