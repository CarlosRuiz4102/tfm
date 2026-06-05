from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import LLMConfig, RESULTS_DIR
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


CATALOG_PATH = ROOT / "data" / "catalog" / "bateria_50_ejemplos.json"
REPORT_PATH = RESULTS_DIR / "reports" / "evaluacion_bateria_50.md"
EVALUATION_DIR = RESULTS_DIR / "evaluations"

FORBIDDEN_TERMS = [
    "recomiendo comprar",
    "recomiendo vender",
    "deberias comprar",
    "deberías comprar",
    "deberias vender",
    "deberías vender",
    "compra ahora",
    "vende ahora",
    "garantiza rentabilidad",
    "seguro que subira",
    "seguro que subirá",
]


def _load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_case_input(case: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(case["input"])
    resolved_paths = []
    for csv_path in payload.get("csv_paths", []):
        path = Path(csv_path)
        if not path.is_absolute():
            path = ROOT / path
        resolved_paths.append(str(path.resolve()))
    payload["csv_paths"] = resolved_paths
    return payload


def _select_cases(cases: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = list(cases)
    if args.levels:
        levels = set(args.levels)
        selected = [case for case in selected if case["level"] in levels]
    if args.cases:
        requested = set(args.cases)
        selected = [case for case in selected if case["id"] in requested]
        missing = sorted(requested - {case["id"] for case in selected})
        if missing:
            raise ValueError(f"Casos no encontrados: {', '.join(missing)}")
    if args.chunk_size is not None:
        if args.chunk_size <= 0:
            raise ValueError("--chunk-size debe ser mayor que cero.")
        if args.chunk_index is None:
            raise ValueError("--chunk-index es obligatorio cuando se usa --chunk-size.")
        if args.chunk_index < 0:
            raise ValueError("--chunk-index debe empezar en 0.")
        start = args.chunk_index * args.chunk_size
        end = start + args.chunk_size
        selected = selected[start:end]
    if args.max_cases is not None:
        selected = selected[: args.max_cases]
    return selected


def _json_block(value: Any, max_chars: int = 3500) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [salida truncada en el informe]"
    return text


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def _text_blob(*values: Any) -> str:
    return " ".join(_compact_text(value).lower() for value in values)


def _has_any_key(output: dict[str, Any], keys: list[str]) -> bool:
    return any(key in output for key in keys)


def _technical_quality(state_dict: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    output = state_dict.get("execution_output") or {}
    final_answer = state_dict.get("final_answer") or ""
    query = case["input"]["query"].lower()
    expected_visual = case["level"] in {"B", "C"} or "serie" in query or "drawdown" in query
    forbidden = [term for term in FORBIDDEN_TERMS if term in final_answer.lower()]
    return {
        "completed": state_dict.get("status") == "completed",
        "has_analysis_plan": bool(state_dict.get("analysis_plan")),
        "has_generated_code": bool(state_dict.get("generated_code")),
        "has_execution_output": bool(output),
        "has_final_answer": bool(final_answer.strip()),
        "has_table_data": isinstance(output, dict)
        and _has_any_key(output, ["table_data", "summary", "ranking_mensual", "monthly_ranking", "metrics"]),
        "has_visual_data_when_expected": (not expected_visual)
        or (
            isinstance(output, dict)
            and _has_any_key(output, ["chart_data", "visualization_data", "drawdown", "normalized_to_100"])
        ),
        "forbidden_terms": forbidden,
        "answer_length_chars": len(final_answer),
    }


def _score_subjective_heuristic(case: dict[str, Any], state_dict: dict[str, Any]) -> dict[str, Any]:
    plan = state_dict.get("analysis_plan") or {}
    output = state_dict.get("execution_output") or {}
    final_answer = state_dict.get("final_answer") or ""
    status = state_dict.get("status")
    quality = _technical_quality(state_dict, case)
    combined = _text_blob(plan, output, final_answer)

    tickers = case["input"].get("tickers") or []
    ticker_hits = sum(1 for ticker in tickers if ticker.lower() in combined)
    level_match = str(plan.get("analysis_level", "")).upper() == case["level"]
    if not plan:
        understanding = 0
    elif ticker_hits == len(tickers) and level_match:
        understanding = 2
    else:
        understanding = 1

    expected_outputs = case.get("expected_outputs") or []
    expected_hits = sum(1 for item in expected_outputs if item.lower().split()[0] in combined)
    metrics = plan.get("metrics") or []
    if not plan:
        metric_relevance = 0
    elif metrics and expected_hits >= max(1, len(expected_outputs) // 3):
        metric_relevance = 2
    else:
        metric_relevance = 1

    if status == "completed" and quality["has_execution_output"]:
        analytical_execution = 2
    elif quality["has_execution_output"] or state_dict.get("execution_returncode") == 0:
        analytical_execution = 1
    else:
        analytical_execution = 0

    if not final_answer.strip() or not output:
        interpretation_fidelity = 0
    elif status == "completed" and not quality["forbidden_terms"]:
        interpretation_fidelity = 2
    else:
        interpretation_fidelity = 1

    if quality["forbidden_terms"]:
        clarity_prudence = 0
    elif status == "completed" and len(final_answer) >= 300:
        clarity_prudence = 2
    elif final_answer.strip():
        clarity_prudence = 1
    else:
        clarity_prudence = 0

    scores = {
        "comprension_consulta": understanding,
        "pertinencia_metricas": metric_relevance,
        "calidad_ejecucion_analitica": analytical_execution,
        "fidelidad_interpretacion": interpretation_fidelity,
        "claridad_utilidad_prudencia": clarity_prudence,
    }
    return {
        "mode": "heuristica_previa_revision_humana",
        "scores": scores,
        "total": sum(scores.values()),
        "max_total": 10,
        "notes": [
            "Estas puntuaciones son una preevaluacion automatica para priorizar revision.",
            "La puntuacion final subjetiva debe confirmarse manualmente con docs/rubrica_evaluacion.md.",
        ],
    }


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    workflow = build_workflow()
    payload = _resolve_case_input(case)
    started = time.perf_counter()
    state = workflow.invoke(FinancialQueryInput.from_dict(payload))
    elapsed = round(time.perf_counter() - started, 2)
    state_dict = state.to_dict()
    state_dict["generated_code"] = state.generated_code
    return {
        "id": case["id"],
        "level": case["level"],
        "objective": case.get("objective"),
        "dataset": case.get("dataset"),
        "expected_outputs": case.get("expected_outputs", []),
        "input": payload,
        "status": state.status,
        "elapsed_seconds": elapsed,
        "analysis_plan": state.analysis_plan,
        "execution_output": state.execution_output,
        "final_answer": state.final_answer,
        "warnings": state.warnings,
        "error_message": state.error_message,
        "artifacts": state.execution_artifacts,
        "quality": _technical_quality(state_dict, case),
        "subjective_metrics": _score_subjective_heuristic(case, state_dict),
    }


def _write_json_at(path: Path, results: list[dict[str, Any]], selected_ids: list[str], catalog: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "catalog": str(CATALOG_PATH),
        "catalog_version": catalog.get("version"),
        "selected_case_ids": selected_ids,
        "results": results,
    }
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _new_json_path() -> Path:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    return EVALUATION_DIR / f"bateria_50_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


def _write_report(results: list[dict[str, Any]], selected: list[dict[str, Any]], json_path: Path, catalog: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    selected_counts = Counter(case["level"] for case in selected)
    result_counts = Counter(result["level"] for result in results)
    completed_counts = Counter(result["level"] for result in results if result["status"] == "completed")
    completed = sum(1 for result in results if result["status"] == "completed")
    elapsed_total = round(sum(result["elapsed_seconds"] for result in results), 2)
    avg_elapsed = round(elapsed_total / len(results), 2) if results else 0
    estimated_full = round(avg_elapsed * 50 / 60, 1) if results else 0
    config = LLMConfig.from_env()

    lines = [
        "# Evaluacion de bateria de 50 ejemplos",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Catalogo: `{CATALOG_PATH}`",
        f"JSON completo de resultados: `{json_path}`",
        "",
        "## Porcentajes de la bateria completa",
        "",
        "| Nivel | Casos | Porcentaje |",
        "|---|---:|---:|",
    ]
    for level in ["A", "B", "C"]:
        count = catalog.get("level_distribution", {}).get(level, 0)
        pct = round((count / 50) * 100, 1)
        lines.append(f"| {level} | {count} | {pct}% |")

    lines.extend(
        [
            "",
            "## Ejecucion realizada",
            "",
            f"- Modelo configurado: `{config.model}`",
            f"- Casos seleccionados: `{len(selected)}`",
            f"- Casos ejecutados: `{len(results)}`",
            f"- Casos completados: `{completed}/{len(results) if results else 0}`",
            f"- Tiempo total observado: `{elapsed_total} s`",
            f"- Tiempo medio por caso: `{avg_elapsed} s`",
            f"- Estimacion lineal para 50 casos con este promedio: `{estimated_full} min`",
            "",
            "La ejecucion completa de 50 casos puede hacerse en una sola llamada si el endpoint es estable, pero es mas robusto fragmentarla.",
            "Recomendacion practica: bloques de 5 o 10 casos usando `--chunk-size 5` o `--chunk-size 10`, porque cada caso hace varias llamadas LLM y puede necesitar reparacion.",
            "",
            "## Cobertura de la ejecucion",
            "",
            "| Nivel | Seleccionados | Ejecutados | Completados |",
            "|---|---:|---:|---:|",
        ]
    )
    for level in ["A", "B", "C"]:
        lines.append(
            f"| {level} | {selected_counts[level]} | {result_counts[level]} | {completed_counts[level]} |"
        )

    lines.extend(
        [
            "",
            "## Matriz de resultados y metricas subjetivas",
            "",
            "Las metricas subjetivas son una preevaluacion heuristica automatica basada en la rubrica. Sirven para revisar rapido, no sustituyen la revision humana final.",
            "",
            "| ID | Nivel | Estado | Tiempo | M1 | M2 | M3 | M4 | M5 | Total |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for result in results:
        scores = result["subjective_metrics"]["scores"]
        lines.append(
            "| `{id}` | {level} | `{status}` | {elapsed} s | {m1} | {m2} | {m3} | {m4} | {m5} | {total}/10 |".format(
                id=result["id"],
                level=result["level"],
                status=result["status"],
                elapsed=result["elapsed_seconds"],
                m1=scores["comprension_consulta"],
                m2=scores["pertinencia_metricas"],
                m3=scores["calidad_ejecucion_analitica"],
                m4=scores["fidelidad_interpretacion"],
                m5=scores["claridad_utilidad_prudencia"],
                total=result["subjective_metrics"]["total"],
            )
        )

    lines.extend(
        [
            "",
            "## Leyenda de metricas subjetivas",
            "",
            "- M1: comprension de la consulta.",
            "- M2: pertinencia de metricas.",
            "- M3: calidad de ejecucion analitica.",
            "- M4: fidelidad de la interpretacion.",
            "- M5: claridad, utilidad y prudencia.",
            "",
            "## Detalle por ejemplo",
            "",
        ]
    )
    for result in results:
        scores = result["subjective_metrics"]["scores"]
        lines.extend(
            [
                f"### {result['id']} - Nivel {result['level']}",
                "",
                f"**Objetivo:** {result['objective']}",
                "",
                f"**Dataset:** `{result['dataset']}`",
                "",
                f"**Estado:** `{result['status']}` en `{result['elapsed_seconds']} s`.",
                "",
                "**Entrada ejecutada:**",
                "",
                "```json",
                _json_block(result["input"], max_chars=2500),
                "```",
                "",
                "**Metricas subjetivas heuristicas:**",
                "",
                f"- M1 comprension de la consulta: `{scores['comprension_consulta']}/2`",
                f"- M2 pertinencia de metricas: `{scores['pertinencia_metricas']}/2`",
                f"- M3 calidad de ejecucion analitica: `{scores['calidad_ejecucion_analitica']}/2`",
                f"- M4 fidelidad de la interpretacion: `{scores['fidelidad_interpretacion']}/2`",
                f"- M5 claridad, utilidad y prudencia: `{scores['claridad_utilidad_prudencia']}/2`",
                f"- Total: `{result['subjective_metrics']['total']}/10`",
                "",
                "**Respuesta final (`state.final_answer`):**",
                "",
                result["final_answer"].strip() or "Sin respuesta final.",
                "",
                "**Salida estructurada del codigo (`state.execution_output`):**",
                "",
                "```json",
                _json_block(result["execution_output"], max_chars=3500),
                "```",
                "",
            ]
        )
        if result["warnings"]:
            lines.extend(["**Warnings:**", "", "```json", _json_block(result["warnings"], max_chars=1600), "```", ""])
        if result["error_message"]:
            lines.extend(["**Error:**", "", _compact_text(result["error_message"]), ""])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta la bateria de 50 ejemplos y genera informe Markdown.")
    parser.add_argument("--catalog", default=str(CATALOG_PATH), help="Ruta del catalogo JSON.")
    parser.add_argument("--levels", nargs="+", choices=["A", "B", "C"], help="Filtra por niveles.")
    parser.add_argument("--cases", nargs="+", help="Filtra por IDs de caso.")
    parser.add_argument("--max-cases", type=int, help="Ejecuta solo los primeros N casos seleccionados.")
    parser.add_argument("--chunk-size", type=int, help="Tamano de bloque para ejecucion fragmentada.")
    parser.add_argument("--chunk-index", type=int, help="Indice de bloque empezando en 0.")
    parser.add_argument("--resume-json", help="JSON previo de resultados para continuar una ejecucion parcial.")
    parser.add_argument("--skip-existing", action="store_true", help="Con --resume-json, omite casos ya presentes.")
    parser.add_argument("--list-only", action="store_true", help="Solo muestra seleccion y porcentajes, no ejecuta.")
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.is_absolute():
        catalog_path = ROOT / catalog_path
    catalog = _load_catalog(catalog_path)
    selected = _select_cases(catalog["cases"], args)

    counts = Counter(case["level"] for case in catalog["cases"])
    print("Porcentajes de la bateria completa:")
    for level in ["A", "B", "C"]:
        pct = round((counts[level] / len(catalog["cases"])) * 100, 1)
        print(f"- Nivel {level}: {counts[level]}/{len(catalog['cases'])} = {pct}%")
    print(f"Casos seleccionados para esta ejecucion: {len(selected)}")

    initial_results: list[dict[str, Any]] = []
    if args.resume_json:
        resume_path = Path(args.resume_json)
        if not resume_path.is_absolute():
            resume_path = ROOT / resume_path
        resume_data = json.loads(resume_path.read_text(encoding="utf-8"))
        initial_results = list(resume_data.get("results") or [])
        print(f"Resultados cargados para continuar: {len(initial_results)}")

    if args.skip_existing and initial_results:
        done_ids = {result["id"] for result in initial_results}
        selected = [case for case in selected if case["id"] not in done_ids]
        print(f"Casos pendientes tras omitir existentes: {len(selected)}")

    if args.list_only:
        for case in selected:
            print(f"{case['id']} ({case['level']})")
        return 0

    report_selected = _select_cases(catalog["cases"], argparse.Namespace(
        levels=args.levels,
        cases=args.cases,
        chunk_size=args.chunk_size,
        chunk_index=args.chunk_index,
        max_cases=args.max_cases,
    ))
    if args.resume_json and not any([args.levels, args.cases, args.chunk_size, args.max_cases]):
        report_selected = list(catalog["cases"])

    results: list[dict[str, Any]] = list(initial_results)
    json_path = _new_json_path()
    selected_ids = [case["id"] for case in report_selected]
    for index, case in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] Ejecutando {case['id']} ({case['level']})...", flush=True)
        results.append(_run_case(case))
        _write_json_at(json_path, results, selected_ids, catalog)
        _write_report(results, report_selected, json_path, catalog)

    _write_json_at(json_path, results, selected_ids, catalog)
    _write_report(results, report_selected, json_path, catalog)
    print(f"Informe escrito en: {REPORT_PATH}")
    print(f"JSON escrito en: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
