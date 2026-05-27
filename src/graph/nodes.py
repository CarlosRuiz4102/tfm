from __future__ import annotations

from src.execution.code_security import validate_generated_code
from src.execution.code_runner import run_generated_code
from src.graph.validation import validate_input
from src.llm.client import LLMClientError
from src.llm.pipeline import build_llm_analysis, build_llm_code, build_llm_interpretation, repair_llm_code
from src.schemas import AnalysisPlan, FinancialQueryInput, WorkflowState


def _compact_for_interpretation(value, max_list_items: int = 40, max_string_chars: int = 2000):
    if isinstance(value, dict):
        return {
            key: _compact_for_interpretation(item, max_list_items=max_list_items, max_string_chars=max_string_chars)
            for key, item in value.items()
        }
    if isinstance(value, list):
        if len(value) <= max_list_items:
            return [
                _compact_for_interpretation(item, max_list_items=max_list_items, max_string_chars=max_string_chars)
                for item in value
            ]
        head_size = max_list_items // 2
        tail_size = max_list_items - head_size
        compacted_items = value[:head_size] + value[-tail_size:]
        return {
            "truncated": True,
            "original_length": len(value),
            "items": [
                _compact_for_interpretation(item, max_list_items=max_list_items, max_string_chars=max_string_chars)
                for item in compacted_items
            ],
        }
    if isinstance(value, str) and len(value) > max_string_chars:
        return value[:max_string_chars] + "... [texto truncado para interpretacion]"
    return value


def ingest_node(state: WorkflowState) -> WorkflowState:
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    errors = validate_input(query_input)
    if errors:
        state.status = "invalid"
        state.error_message = " | ".join(errors)
        return state
    state.status = "ingested"
    return state


def llm_analysis_node(state: WorkflowState) -> WorkflowState:
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    try:
        plan, warnings = build_llm_analysis(query_input)
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    state.analysis_plan = plan.to_dict()
    state.status = "planned"
    return state


def code_generation_node(state: WorkflowState) -> WorkflowState:
    if not state.analysis_plan:
        state.status = "error"
        state.error_message = "No existe analysis_plan para generar codigo."
        return state

    plan = AnalysisPlan(**state.analysis_plan)
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    try:
        code_output, warnings = build_llm_code(query_input, plan)
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    state.generated_code = code_output
    state.status = "code_generated"
    return state


def code_security_node(state: WorkflowState) -> WorkflowState:
    if not state.generated_code:
        state.status = "error"
        state.error_message = "No existe generated_code para validar."
        return state

    result = validate_generated_code(state.generated_code)
    if not result.is_valid:
        if state.analysis_plan:
            plan = AnalysisPlan(**state.analysis_plan)
            query_input = FinancialQueryInput.from_dict(state.normalized_query)
            error_detail = "Codigo rechazado por seguridad: " + " | ".join(result.errors)
            try:
                repaired_code, warnings = repair_llm_code(query_input, plan, state.generated_code, error_detail)
                repaired_result = validate_generated_code(repaired_code)
                if repaired_result.is_valid:
                    state.generated_code = repaired_code
                    state.warnings.extend(warnings)
                    state.status = "code_validated"
                    return state
                result = repaired_result
            except LLMClientError as exc:
                state.warnings.append(str(exc))
        state.status = "code_rejected"
        state.error_message = "Codigo rechazado por seguridad: " + " | ".join(result.errors)
        return state
    state.status = "code_validated"
    return state


def code_execution_node(state: WorkflowState) -> WorkflowState:
    if not state.generated_code or not state.analysis_plan:
        state.status = "error"
        state.error_message = "Faltan generated_code o analysis_plan."
        return state

    payload = {
        "query": state.user_query,
        "tickers": state.normalized_query["tickers"],
        "csv_paths": state.csv_paths,
        "start": state.normalized_query.get("start"),
        "end": state.normalized_query.get("end"),
        "period": state.normalized_query.get("period"),
        "interval": state.normalized_query.get("interval"),
        "input": state.normalized_query,
        "analysis_plan": state.analysis_plan,
    }
    execution = run_generated_code(state.generated_code, payload)
    if execution.returncode != 0:
        plan = AnalysisPlan(**state.analysis_plan)
        query_input = FinancialQueryInput.from_dict(state.normalized_query)
        error_detail = execution.stderr.strip() or "El script fallo sin stderr."
        try:
            repaired_code, warnings = repair_llm_code(query_input, plan, state.generated_code, error_detail)
            repaired_result = validate_generated_code(repaired_code)
            if repaired_result.is_valid:
                state.generated_code = repaired_code
                state.warnings.extend(warnings)
                execution = run_generated_code(repaired_code, payload)
            else:
                state.warnings.append("La reparacion no supero seguridad: " + " | ".join(repaired_result.errors))
        except LLMClientError as exc:
            state.warnings.append(str(exc))
    state.execution_stdout = execution.stdout
    state.execution_stderr = execution.stderr
    state.execution_returncode = execution.returncode
    state.execution_output = execution.parsed_output
    state.execution_artifacts = execution.artifacts.to_dict()
    state.status = "executed" if execution.returncode == 0 else "execution_failed"
    return state


def interpretation_node(state: WorkflowState) -> WorkflowState:
    output = state.execution_output or {}
    if state.execution_returncode != 0:
        return execution_error_node(state)
    if not state.analysis_plan:
        state.status = "completed_with_error"
        state.error_message = "No existe analysis_plan para interpretar resultados."
        state.final_answer = state.error_message
        return state

    plan = AnalysisPlan(**state.analysis_plan)
    output_for_llm = _compact_for_interpretation(output)
    try:
        final_answer, warnings = build_llm_interpretation(output_for_llm, plan)
    except LLMClientError as exc:
        state.status = "completed_with_error"
        state.error_message = str(exc)
        state.final_answer = (
            "No se pudo generar una respuesta final con LLM. "
            f"Detalle: {exc}"
        )
        return state

    state.warnings.extend(warnings)
    state.final_answer = final_answer
    state.status = "completed"
    return state


def invalid_request_node(state: WorkflowState) -> WorkflowState:
    state.final_answer = state.error_message or "La peticion es invalida."
    state.status = "completed_with_error"
    return state


def execution_error_node(state: WorkflowState) -> WorkflowState:
    if state.error_message:
        state.final_answer = state.error_message
        state.status = "completed_with_error"
        return state

    state.final_answer = (
        "El script generado fallo durante la ejecucion. "
        f"stderr: {state.execution_stderr.strip() or 'sin detalle adicional'}"
    )
    state.status = "completed_with_error"
    return state
