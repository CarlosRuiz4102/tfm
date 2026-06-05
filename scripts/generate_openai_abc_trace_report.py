from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_abc_demo_report import DEMO_CASES
from src.config import LLMConfig, RESULTS_DIR
from src.execution.code_runner import run_generated_code
from src.execution.code_security import validate_generated_code
from src.graph.nodes import _compact_for_interpretation
from src.graph.validation import validate_input
from src.llm.client import LLMClientError, create_llm_client
from src.llm.pipeline import _code_from_text, _json_from_text, repair_llm_code
from src.llm.prompts import build_analysis_messages, build_codegen_messages, build_interpretation_messages
from src.schemas import AnalysisPlan, FinancialQueryInput


REPORT_PATH = RESULTS_DIR / "reports" / "flujo_completo_openai_abc.md"
SELECTED_CASE_IDS = [
    "level_a_nvda_growth",
    "level_b_qqq_spy_clear_compare",
    "stress_visual_qqq_spy_monthly",
]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _messages_to_dict(messages: list[Any]) -> list[dict[str, str]]:
    return [message.to_dict() for message in messages]


def _fence(language: str, value: str) -> str:
    return f"```{language}\n{value.rstrip()}\n```"


def _case_map() -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in DEMO_CASES}


def _run_case(case: dict[str, Any], llm_config: LLMConfig) -> dict[str, Any]:
    started = time.perf_counter()
    trace: dict[str, Any] = {
        "case": case,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "status": "started",
        "warnings": [],
        "failures": [],
        "timings": {},
    }
    query_input = FinancialQueryInput.from_dict(case["input"])
    trace["normalized_input"] = query_input.to_dict()

    validation_errors = validate_input(query_input)
    trace["input_validation"] = {
        "status": "valid" if not validation_errors else "invalid",
        "errors": validation_errors,
    }
    if validation_errors:
        trace["status"] = "invalid_input"
        trace["failures"].extend(validation_errors)
        trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        return trace

    analysis_messages = build_analysis_messages(query_input)
    trace["agent_1_input_messages"] = _messages_to_dict(analysis_messages)

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError(
                "No se pudo crear cliente LLM porque VLLM_API_KEY/OPENAI_API_KEY/LLM_API_KEY no esta configurada "
                "o contiene un valor placeholder."
            )
    except Exception as exc:
        trace["status"] = "llm_client_error"
        trace["failures"].append(str(exc))
        trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        return trace

    # Agent 1
    t0 = time.perf_counter()
    try:
        analysis_response = client.complete_json(analysis_messages)
        analysis_payload = _json_from_text(analysis_response.content)
        analysis_level = str(analysis_payload.get("analysis_level") or "A").strip().upper()
        if analysis_level not in {"A", "B", "C"}:
            analysis_level = "A"
        plan = AnalysisPlan(
            analysis_level=analysis_level,
            analytical_goal=str(analysis_payload.get("analytical_goal") or query_input.query).strip(),
            analysis_type=str(analysis_payload.get("analysis_type") or "historical_financial_analysis").strip(),
            metrics=[str(item) for item in analysis_payload.get("metrics") or []],
            required_columns=[str(item) for item in analysis_payload.get("required_columns") or []],
            data_requirements=[str(item) for item in analysis_payload.get("data_requirements") or []],
            output_requirements=[str(item) for item in analysis_payload.get("output_requirements") or []],
            presentation_preferences=[str(item) for item in analysis_payload.get("presentation_preferences") or []],
            reasoning=str(analysis_payload.get("reasoning") or "").strip(),
        )
        trace["agent_1_raw_response"] = analysis_response.content
        trace["analysis_plan"] = plan.to_dict()
        trace["timings"]["agent_1_seconds"] = round(time.perf_counter() - t0, 2)
    except Exception as exc:
        trace["status"] = "agent_1_failed"
        trace["failures"].append(str(exc))
        trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        return trace

    # Agent 2
    t0 = time.perf_counter()
    codegen_messages = build_codegen_messages(query_input, plan)
    trace["agent_2_input_messages"] = _messages_to_dict(codegen_messages)
    try:
        code_response = client.complete_json(codegen_messages)
        generated_code = _code_from_text(code_response.content)
        trace["agent_2_raw_response"] = code_response.content
        trace["generated_code"] = generated_code
        trace["timings"]["agent_2_seconds"] = round(time.perf_counter() - t0, 2)
    except Exception as exc:
        trace["status"] = "agent_2_failed"
        trace["failures"].append(str(exc))
        trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        return trace

    # Security and optional repair.
    security_result = validate_generated_code(generated_code)
    trace["security_validation"] = {
        "is_valid": security_result.is_valid,
        "errors": security_result.errors,
        "warnings": getattr(security_result, "warnings", []),
    }
    if not security_result.is_valid:
        error_detail = "Codigo rechazado por seguridad: " + " | ".join(security_result.errors)
        trace["failures"].append(error_detail)
        try:
            repaired_code, repair_warnings = repair_llm_code(query_input, plan, generated_code, error_detail)
            repaired_security = validate_generated_code(repaired_code)
            trace["repair_after_security"] = {
                "warnings": repair_warnings,
                "code": repaired_code,
                "security": {
                    "is_valid": repaired_security.is_valid,
                    "errors": repaired_security.errors,
                    "warnings": getattr(repaired_security, "warnings", []),
                },
            }
            if repaired_security.is_valid:
                generated_code = repaired_code
                trace["generated_code"] = generated_code
                trace["warnings"].extend(repair_warnings)
                trace["security_validation"] = trace["repair_after_security"]["security"]
            else:
                trace["status"] = "code_rejected"
                trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
                return trace
        except Exception as exc:
            trace["status"] = "code_rejected_repair_failed"
            trace["failures"].append(str(exc))
            trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
            return trace

    # Execution and optional repair.
    execution_payload = {
        "query": query_input.query,
        "tickers": query_input.tickers,
        "csv_paths": query_input.csv_paths,
        "start": query_input.start,
        "end": query_input.end,
        "period": query_input.period,
        "interval": query_input.interval,
        "input": query_input.to_dict(),
        "analysis_plan": plan.to_dict(),
    }
    trace["execution_payload"] = execution_payload
    t0 = time.perf_counter()
    execution = run_generated_code(generated_code, execution_payload)
    trace["timings"]["execution_seconds"] = round(time.perf_counter() - t0, 2)
    trace["execution"] = execution.to_dict()

    if execution.returncode != 0:
        error_detail = execution.stderr.strip() or "El script fallo sin stderr."
        trace["failures"].append("Fallo de ejecucion inicial: " + error_detail)
        try:
            repaired_code, repair_warnings = repair_llm_code(query_input, plan, generated_code, error_detail)
            repaired_security = validate_generated_code(repaired_code)
            trace["repair_after_execution"] = {
                "warnings": repair_warnings,
                "code": repaired_code,
                "security": {
                    "is_valid": repaired_security.is_valid,
                    "errors": repaired_security.errors,
                    "warnings": getattr(repaired_security, "warnings", []),
                },
            }
            if repaired_security.is_valid:
                generated_code = repaired_code
                trace["generated_code"] = generated_code
                trace["warnings"].extend(repair_warnings)
                t0 = time.perf_counter()
                execution = run_generated_code(generated_code, execution_payload)
                trace["timings"]["repaired_execution_seconds"] = round(time.perf_counter() - t0, 2)
                trace["execution"] = execution.to_dict()
            else:
                trace["warnings"].append("La reparacion no supero seguridad.")
        except Exception as exc:
            trace["warnings"].append("No se pudo reparar la ejecucion: " + str(exc))

    if execution.returncode != 0:
        trace["status"] = "execution_failed"
        trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        return trace

    # Agent 3
    output_for_llm = _compact_for_interpretation(execution.parsed_output or {})
    interpretation_messages = build_interpretation_messages(output_for_llm, plan)
    trace["agent_3_input_messages"] = _messages_to_dict(interpretation_messages)
    t0 = time.perf_counter()
    try:
        interpretation_response = client.complete_text(interpretation_messages)
        trace["agent_3_raw_response"] = interpretation_response.content
        trace["final_answer"] = interpretation_response.content.strip()
        trace["timings"]["agent_3_seconds"] = round(time.perf_counter() - t0, 2)
        trace["status"] = "completed"
    except Exception as exc:
        trace["status"] = "agent_3_failed"
        trace["failures"].append(str(exc))

    trace["elapsed_seconds"] = round(time.perf_counter() - started, 2)
    return trace


def _write_case(lines: list[str], trace: dict[str, Any]) -> None:
    case = trace["case"]
    lines.extend(
        [
            f"## Caso {case['level']} - `{case['id']}`",
            "",
            f"**Consulta:** {case['input']['query']}",
            "",
            f"**Objetivo esperado:** {case['expected_depth']}",
            "",
            f"**Estado final:** `{trace['status']}`",
            "",
            f"**Tiempo total:** `{trace.get('elapsed_seconds', 'n/d')} s`",
            "",
            "### Fallos y avisos",
            "",
        ]
    )
    failures = trace.get("failures") or []
    warnings = trace.get("warnings") or []
    if not failures and not warnings:
        lines.append("- Sin fallos ni avisos registrados.")
    for failure in failures:
        lines.append(f"- Fallo: {failure}")
    for warning in warnings:
        lines.append(f"- Aviso: {warning}")
    lines.extend(["", "### 0. Entrada normalizada", "", _fence("json", _json(trace.get("normalized_input"))), ""])
    lines.extend(["### 1. Validacion inicial", "", _fence("json", _json(trace.get("input_validation"))), ""])

    if "agent_1_input_messages" in trace:
        lines.extend(["### 2. Agente 1 - entrada", "", _fence("json", _json(trace["agent_1_input_messages"])), ""])
    if "agent_1_raw_response" in trace:
        lines.extend(["### 3. Agente 1 - salida bruta", "", _fence("json", trace["agent_1_raw_response"]), ""])
    if "analysis_plan" in trace:
        lines.extend(["### 4. Plan normalizado usado por el sistema", "", _fence("json", _json(trace["analysis_plan"])), ""])
    if "agent_2_input_messages" in trace:
        lines.extend(["### 5. Agente 2 - entrada", "", _fence("json", _json(trace["agent_2_input_messages"])), ""])
    if "agent_2_raw_response" in trace:
        lines.extend(["### 6. Agente 2 - salida bruta", "", _fence("json", trace["agent_2_raw_response"]), ""])
    if "generated_code" in trace:
        lines.extend(["### 7. Codigo Python generado/ejecutado", "", _fence("python", trace["generated_code"]), ""])
    if "security_validation" in trace:
        lines.extend(["### 8. Validacion de seguridad", "", _fence("json", _json(trace["security_validation"])), ""])
    if "execution_payload" in trace:
        lines.extend(["### 9. Payload de ejecucion del script", "", _fence("json", _json(trace["execution_payload"])), ""])
    if "execution" in trace:
        execution = trace["execution"]
        lines.extend(
            [
                "### 10. Resultado de ejecucion",
                "",
                "**Artefactos generados:**",
                "",
                _fence("json", _json(execution.get("artifacts"))),
                "",
                "**Return code / stderr / stdout parseado:**",
                "",
                _fence(
                    "json",
                    _json(
                        {
                            "returncode": execution.get("returncode"),
                            "stderr": execution.get("stderr"),
                            "parsed_output": execution.get("parsed_output"),
                        }
                    ),
                ),
                "",
            ]
        )
    if "repair_after_security" in trace:
        lines.extend(["### Reparacion tras seguridad", "", _fence("json", _json(trace["repair_after_security"])), ""])
    if "repair_after_execution" in trace:
        lines.extend(["### Reparacion tras ejecucion", "", _fence("json", _json(trace["repair_after_execution"])), ""])
    if "agent_3_input_messages" in trace:
        lines.extend(["### 11. Agente 3 - entrada", "", _fence("json", _json(trace["agent_3_input_messages"])), ""])
    if "agent_3_raw_response" in trace:
        lines.extend(["### 12. Agente 3 - salida / respuesta final", "", trace["agent_3_raw_response"].strip(), ""])
    if "timings" in trace:
        lines.extend(["### Tiempos por fase", "", _fence("json", _json(trace["timings"])), ""])


def main() -> None:
    llm_config = LLMConfig.from_env()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cases = _case_map()
    selected = [cases[case_id] for case_id in SELECTED_CASE_IDS]
    traces = [_run_case(case, llm_config) for case in selected]

    lines: list[str] = [
        "# Flujo completo OpenAI A/B/C",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Este informe registra una ejecucion real del flujo para un caso de Nivel A, uno de Nivel B y uno de Nivel C. "
        "No incluye claves ni secretos. Las rutas de artefactos corresponden al entorno local de ejecucion.",
        "",
        "## Configuracion LLM usada",
        "",
        _fence(
            "json",
            _json(
                {
                    "provider": llm_config.provider,
                    "profile": llm_config.profile,
                    "model": llm_config.model,
                    "base_url_configured": bool(llm_config.base_url),
                    "temperature": llm_config.temperature,
                    "max_tokens": llm_config.max_tokens,
                    "timeout_seconds": llm_config.timeout_seconds,
                    "configured": llm_config.is_configured,
                }
            ),
        ),
        "",
    ]
    for trace in traces:
        _write_case(lines, trace)
        lines.append("---")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(str(REPORT_PATH))


if __name__ == "__main__":
    main()
