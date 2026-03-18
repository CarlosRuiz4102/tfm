from __future__ import annotations

from src.execution.code_runner import run_generated_code
from src.prompts import build_analysis_plan, build_code_template
from src.schemas import FinancialQueryInput, WorkflowState
from src.graph.routing import route_intent, validate_input


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
    plan = build_analysis_plan(query_input)
    state.analysis_plan = plan.to_dict()
    state.status = "planned"
    return state


def code_generation_node(state: WorkflowState) -> WorkflowState:
    if not state.analysis_plan:
        state.status = "error"
        state.error_message = "No existe analysis_plan para generar codigo."
        return state

    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    plan = build_analysis_plan(query_input)
    code_output = build_code_template(plan)
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

    intent = output.get("intent")
    if intent == "price_growth":
        summary = output["summary"]
        state.final_answer = (
            f"{summary['ticker']} paso de {summary['start_close']:.2f} a {summary['end_close']:.2f} "
            f"entre {summary['start_date']} y {summary['end_date']}. "
            f"La variacion absoluta fue {summary['absolute_growth']:.2f} y la variacion porcentual "
            f"fue {summary['percentage_growth']:.2f}%."
        )
    elif intent == "compare_assets":
        comparisons = output["comparisons"]
        parts = []
        for item in comparisons:
            parts.append(
                f"{item['ticker']} cambio {item['percentage_growth']:.2f}% "
                f"({item['start_close']:.2f} -> {item['end_close']:.2f})"
            )
        state.final_answer = (
            f"Comparativa completada. {'; '.join(parts)}. "
            f"El mejor comportamiento fue {output['winner']}."
        )
    else:
        state.final_answer = "La ejecucion termino, pero no se pudo interpretar la salida."

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
