from __future__ import annotations

from src.execution.code_runner import run_generated_code
from src.agents import interpret_agent_output
from src.graph.routing import route_intent, validate_input
from src.graph.prompts import build_analysis_plan, build_code_template
from src.llm.pipeline import maybe_build_llm_code, maybe_build_llm_interpretation, maybe_build_llm_plan
from src.schemas import AnalysisPlan, FinancialQueryInput, WorkflowState


def ingest_node(state: WorkflowState) -> WorkflowState:
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    errors = validate_input(query_input)
    if errors:
        state.status = "invalid"
        state.error_message = " | ".join(errors)
        return state
    state.status = "ingested"
    return state


def orchestrator_router_node(state: WorkflowState) -> WorkflowState:
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    router_output = route_intent(query_input)
    state.selected_agent = router_output.selected_agent
    state.warnings.extend(router_output.warnings)
    if not router_output.is_valid:
        state.status = "invalid"
        state.error_message = router_output.error_message
        return state
    state.status = "routed"
    return state


def specialist_analysis_node(state: WorkflowState) -> WorkflowState:
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    fallback_plan = build_analysis_plan(query_input)
    plan, warnings = maybe_build_llm_plan(query_input, fallback_plan)
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
    fallback_code = build_code_template(plan)
    code_output, warnings = maybe_build_llm_code(plan, fallback_code)
    state.warnings.extend(warnings)
    state.generated_code = code_output
    state.status = "code_generated"
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
        "analysis_plan": state.analysis_plan,
    }
    execution = run_generated_code(state.generated_code, payload)
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

    fallback_answer = interpret_agent_output(output)
    final_answer, warnings = maybe_build_llm_interpretation(output, fallback_answer)
    state.warnings.extend(warnings)
    state.final_answer = final_answer
    state.status = "completed"
    return state


def invalid_request_node(state: WorkflowState) -> WorkflowState:
    state.final_answer = state.error_message or "La peticion es invalida."
    state.status = "completed_with_error"
    return state


def execution_error_node(state: WorkflowState) -> WorkflowState:
    state.final_answer = (
        "El script generado fallo durante la ejecucion. "
        f"stderr: {state.execution_stderr.strip() or 'sin detalle adicional'}"
    )
    state.status = "completed_with_error"
    return state
