from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_qualitative_demo_report import DEMO_CASES
from src.config import LLMConfig, RESULTS_DIR
from src.execution.market_data import load_close_prices
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


DEFAULT_PROFILES = ["groq", "gemini", "university"]
DEFAULT_CASE_IDS = [case["id"] for case in DEMO_CASES]

REPORT_PATH = RESULTS_DIR / "reports" / "evaluacion_15_queries_llms.md"
FIGURES_DIR = RESULTS_DIR / "reports" / "figures" / "evaluacion_amplitud_llm"
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
]


def _case_by_id() -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in DEMO_CASES}


def _run_case(profile: str, case: dict[str, Any]) -> dict[str, Any]:
    os.environ["LLM_PROFILE"] = profile
    config = LLMConfig.from_env()
    started = time.perf_counter()
    workflow = build_workflow()
    state = workflow.invoke(FinancialQueryInput.from_dict(case["input"]))
    elapsed = round(time.perf_counter() - started, 2)
    final_answer = state.final_answer or ""
    execution_output = state.execution_output or {}
    warnings = list(state.warnings)
    normalized_answer = final_answer.lower()
    forbidden = [term for term in FORBIDDEN_TERMS if term in normalized_answer]
    expected_visual = case["level"] in {"B", "C"} or "grafica" in case["input"]["query"].lower()
    has_visual_data = isinstance(execution_output, dict) and any(
        key in execution_output for key in ["chart_data", "visualization_data", "drawdown", "normalized_to_100"]
    )
    has_table_data = isinstance(execution_output, dict) and any(
        key in execution_output for key in ["table_data", "ranking_mensual", "summary", "metrics"]
    )
    return {
        "profile": profile,
        "model": config.model,
        "case_id": case["id"],
        "level": case["level"],
        "query": case["input"]["query"],
        "expected_depth": case["expected_depth"],
        "status": state.status,
        "elapsed_seconds": elapsed,
        "analysis_plan": state.analysis_plan,
        "execution_output": execution_output,
        "final_answer": final_answer,
        "warnings": warnings,
        "error_message": state.error_message,
        "artifacts": state.execution_artifacts,
        "quality": {
            "completed": state.status == "completed",
            "has_analysis_plan": bool(state.analysis_plan),
            "has_execution_output": bool(execution_output),
            "has_final_answer": bool(final_answer.strip()),
            "has_table_data": has_table_data,
            "has_visual_data_when_expected": (not expected_visual) or has_visual_data,
            "forbidden_terms": forbidden,
            "answer_length_chars": len(final_answer),
        },
    }


def _json_block(value: Any, max_chars: int = 4500) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [salida truncada en el informe]"
    return text


def _safe(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def _status_label(result: dict[str, Any]) -> str:
    if result["status"] == "completed":
        return "Completa"
    if result["analysis_plan"] and result["execution_output"]:
        return "Parcial: calcula, falla interpretacion"
    if result["analysis_plan"]:
        return "Parcial: planifica, falla codegen/ejecucion"
    return "Falla al iniciar"


def _build_visual_assets() -> dict[str, str]:
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cases = _case_by_id()
    payload = cases["level_b_qqq_spy_clear_compare"]["input"]
    close = load_close_prices(payload["csv_paths"], payload["tickers"])
    normalized = close.divide(close.iloc[0]).multiply(100)
    drawdown = close.divide(close.cummax()).subtract(1).multiply(100)

    normalized_path = FIGURES_DIR / "qqq_spy_normalizada_2024.png"
    drawdown_path = FIGURES_DIR / "qqq_spy_drawdown_2024.png"

    ax = normalized.plot(figsize=(9, 4), linewidth=1.8)
    ax.set_title("QQQ vs SPY 2024 - Evolucion normalizada base 100")
    ax.set_ylabel("Base 100")
    ax.set_xlabel("Fecha")
    ax.grid(True, alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(normalized_path, dpi=160)
    plt.close(ax.figure)

    ax = drawdown.plot(figsize=(9, 4), linewidth=1.8)
    ax.set_title("QQQ vs SPY 2024 - Drawdown historico")
    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("Fecha")
    ax.grid(True, alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(drawdown_path, dpi=160)
    plt.close(ax.figure)

    return {
        "normalized": str(normalized_path),
        "drawdown": str(drawdown_path),
    }


def _build_completion_chart(results: list[dict[str, Any]]) -> str:
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(results)
    pivot = frame.assign(completed=frame["status"].eq("completed").astype(int)).pivot_table(
        index="profile",
        columns="level",
        values="completed",
        aggfunc="sum",
        fill_value=0,
    )
    for level in ["A", "B", "C"]:
        if level not in pivot.columns:
            pivot[level] = 0
    pivot = pivot[["A", "B", "C"]]
    chart_path = FIGURES_DIR / "completitud_por_modelo_nivel.png"
    ax = pivot.plot(kind="bar", figsize=(8, 4), rot=0)
    ax.set_title("Casos completados por perfil y nivel")
    ax.set_ylabel("Casos completados")
    ax.set_xlabel("Perfil LLM")
    ax.grid(axis="y", alpha=0.25)
    ax.figure.tight_layout()
    ax.figure.savefig(chart_path, dpi=160)
    plt.close(ax.figure)
    return str(chart_path)


def _write_json(results: list[dict[str, Any]], profiles: list[str], cases: list[str]) -> Path:
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "profiles": profiles,
        "cases": cases,
        "results": results,
    }
    path = EVALUATION_DIR / f"progressive_llm_scope_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_report(results: list[dict[str, Any]], json_path: Path, figure_paths: dict[str, str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    completion_chart = _build_completion_chart(results)
    completed = sum(1 for result in results if result["status"] == "completed")
    total = len(results)
    quota_limited_profiles = sorted(
        {
            result["profile"]
            for result in results
            if "quota" in (result.get("error_message") or "").lower()
            or "resource_exhausted" in (result.get("error_message") or "").lower()
        }
    )
    quick_notes = [
        f"- Casos completados: `{completed}/{total}`.",
        "- Un caso se considera completo si llega a interpretacion final con estado `completed`.",
        "- Los casos parciales tambien son informativos: muestran si el modelo entiende la consulta, genera codigo, ejecuta metricas o falla en la interpretacion.",
    ]
    if quota_limited_profiles:
        profile_list = ", ".join(f"`{profile}`" for profile in quota_limited_profiles)
        quick_notes.append(
            f"- Aviso metodologico: {profile_list} alcanzo el limite de cuota durante esta ejecucion. "
            "Sus fallos posteriores por `429 RESOURCE_EXHAUSTED` describen la disponibilidad de la API, "
            "no la capacidad intrinseca del modelo."
        )
    lines = [
        "# Evaluacion de amplitud del TFM con LLMs",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Este informe evalua si el MVP mantiene el flujo completo al aumentar la dificultad de las queries.",
        "Se prueban casos simples, mejorados, profesionales y una query de estres visual con varios requisitos de salida.",
        "",
        f"JSON completo de resultados: `{json_path}`",
        "",
        "## Lectura rapida",
        "",
        *quick_notes,
        "",
        "![Completitud por modelo y nivel](" + completion_chart.replace("\\", "/") + ")",
        "",
        "## Visualizaciones base de la bateria",
        "",
        "Estas graficas se generan localmente desde los CSV reales y sirven como referencia visual para las queries B/C sobre QQQ y SPY.",
        "",
        "![QQQ vs SPY normalizada](" + figure_paths["normalized"].replace("\\", "/") + ")",
        "",
        "![QQQ vs SPY drawdown](" + figure_paths["drawdown"].replace("\\", "/") + ")",
        "",
        "## Matriz de resultados",
        "",
        "| Perfil | Modelo | Query | Nivel | Estado | Lectura | Tiempo |",
        "|---|---|---|---:|---|---|---:|",
    ]
    for result in results:
        lines.append(
            "| {profile} | `{model}` | `{case}` | {level} | `{status}` | {label} | {elapsed} s |".format(
                profile=result["profile"],
                model=result["model"],
                case=result["case_id"],
                level=result["level"],
                status=result["status"],
                label=_status_label(result),
                elapsed=result["elapsed_seconds"],
            )
        )

    lines.extend(
        [
            "",
            "## Cobertura por perfil y nivel",
            "",
            "| Perfil | Nivel A | Nivel B | Nivel C | Total |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    profiles = sorted({result["profile"] for result in results})
    for profile in profiles:
        subset = [result for result in results if result["profile"] == profile]
        level_cells = []
        for level in ["A", "B", "C"]:
            level_subset = [result for result in subset if result["level"] == level]
            level_ok = sum(1 for result in level_subset if result["status"] == "completed")
            level_cells.append(f"`{level_ok}/{len(level_subset)}`")
        total_ok = sum(1 for result in subset if result["status"] == "completed")
        lines.append(f"| {profile} | {' | '.join(level_cells)} | `{total_ok}/{len(subset)}` |")

    lines.extend(
        [
            "",
            "## Analisis por perfil",
            "",
        ]
    )
    for profile in profiles:
        subset = [result for result in results if result["profile"] == profile]
        ok = sum(1 for result in subset if result["status"] == "completed")
        partial = sum(1 for result in subset if result["status"] != "completed" and result["analysis_plan"])
        lines.extend(
            [
                f"### {profile}",
                "",
                f"- Completados: `{ok}/{len(subset)}`.",
                f"- Parciales con plan LLM: `{partial}`.",
            ]
        )
        if any(result["quality"]["forbidden_terms"] for result in subset):
            lines.append("- Se detectaron terminos de recomendacion de inversion en alguna respuesta.")
        else:
            lines.append("- No se detectaron recomendaciones explicitas de compra/venta en las respuestas completadas.")
        lines.append("")

    lines.extend(["## Detalle por ejecucion", ""])
    for result in results:
        lines.extend(
            [
                f"### {result['profile']} - {result['case_id']} - Nivel {result['level']}",
                "",
                f"**Query:** {result['query']}",
                "",
                f"**Estado:** `{result['status']}`. **Lectura:** {_status_label(result)}. **Tiempo:** {result['elapsed_seconds']} s.",
                "",
                "**Calidad observada:**",
                "",
                f"- Plan generado: `{result['quality']['has_analysis_plan']}`.",
                f"- Salida de ejecucion: `{result['quality']['has_execution_output']}`.",
                f"- Tabla/datos estructurados: `{result['quality']['has_table_data']}`.",
                f"- Datos visuales si se esperaban: `{result['quality']['has_visual_data_when_expected']}`.",
                f"- Respuesta final: `{result['quality']['has_final_answer']}`.",
                "",
                "**Plan del primer agente:**",
                "",
                "```json",
                _json_block(result["analysis_plan"], max_chars=2500),
                "```",
                "",
                "**Salida estructurada del codigo:**",
                "",
                "```json",
                _json_block(result["execution_output"], max_chars=3200),
                "```",
                "",
                "**Respuesta que veria el usuario:**",
                "",
                result["final_answer"].strip() or "Sin respuesta final.",
                "",
            ]
        )
        if result["warnings"]:
            lines.extend(["**Avisos:**", "", "```json", _json_block(result["warnings"], max_chars=1600), "```", ""])
        if result["error_message"]:
            lines.extend(["**Error registrado:**", "", _safe(result["error_message"]), ""])

    lines.extend(
        [
            "## Conclusiones para la memoria",
            "",
            "- La bateria progresiva permite demostrar aumento de dificultad: Nivel A valida consultas simples, Nivel B obliga a estructura tabular/visual y Nivel C exige formato profesional.",
            "- Los fallos no son ruido: ayudan a documentar limites reales de proveedor, cuota, tamano de salida, formato JSON y reparacion de codigo.",
            "- El ajuste de compactacion de salidas visuales es necesario para que el segundo agente no reciba series completas excesivas.",
            "- La evaluacion debe presentarse como exploratoria y cualitativa, no como una prueba estadistica definitiva.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalua amplitud progresiva del TFM en varios perfiles LLM.")
    parser.add_argument("--profiles", nargs="+", default=DEFAULT_PROFILES)
    parser.add_argument("--cases", nargs="+", default=DEFAULT_CASE_IDS)
    args = parser.parse_args()

    cases_by_id = _case_by_id()
    selected_cases = []
    for case_id in args.cases:
        if case_id not in cases_by_id:
            raise ValueError(f"Caso no reconocido: {case_id}")
        selected_cases.append(cases_by_id[case_id])

    results: list[dict[str, Any]] = []
    for profile in args.profiles:
        for case in selected_cases:
            print(f"Ejecutando {profile} / {case['id']} ({case['level']})...", flush=True)
            results.append(_run_case(profile, case))

    figure_paths = _build_visual_assets()
    json_path = _write_json(results, args.profiles, args.cases)
    _write_report(results, json_path, figure_paths)
    print(f"Informe escrito en: {REPORT_PATH}")
    print(f"JSON escrito en: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
