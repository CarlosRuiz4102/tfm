from __future__ import annotations

from dataclasses import replace
from typing import Callable

from src.graph.nodes import (
    code_execution_node,
    code_generation_node,
    code_security_node,
    execution_error_node,
    ingest_node,
    interpretation_node,
    invalid_request_node,
    llm_analysis_node,
)
from src.schemas import FinancialQueryInput, WorkflowState


NodeFn = Callable[[WorkflowState], WorkflowState]


class SimpleFinancialWorkflow:
    def __init__(self) -> None:
        self.pipeline: list[NodeFn] = [
            ingest_node,
            llm_analysis_node,
            code_generation_node,
            code_security_node,
            code_execution_node,
            interpretation_node,
        ]

    def invoke(self, query_input: FinancialQueryInput) -> WorkflowState:
        state = WorkflowState.from_input(query_input)
        for node in self.pipeline:
            state = node(state)
            if state.status == "invalid":
                return invalid_request_node(state)
            if state.status == "error":
                return execution_error_node(state)
            if state.status == "code_rejected":
                return execution_error_node(state)
            if state.status == "execution_failed":
                return execution_error_node(state)
        return state


def build_workflow() -> SimpleFinancialWorkflow:
    try:
        from langgraph.graph import END, START, StateGraph  # type: ignore
    except ImportError:
        return SimpleFinancialWorkflow()

    graph = StateGraph(WorkflowState)
    graph.add_node("ingest", ingest_node)
    graph.add_node("llm_analysis", llm_analysis_node)
    graph.add_node("code_generation", code_generation_node)
    graph.add_node("code_security", code_security_node)
    graph.add_node("code_execution", code_execution_node)
    graph.add_node("interpretation", interpretation_node)
    graph.add_node("invalid_request", invalid_request_node)
    graph.add_node("execution_error", execution_error_node)

    graph.add_edge(START, "ingest")

    def route_after_execution(state: WorkflowState) -> str:
        return "execution_error" if state.execution_returncode else "interpretation"

    def route_after_llm_step(state: WorkflowState) -> str:
        return "execution_error" if state.status == "error" else "next"

    def route_after_validation(state: WorkflowState) -> str:
        return "invalid_request" if state.status == "invalid" else "next"

    def route_after_security(state: WorkflowState) -> str:
        return "execution_error" if state.status in {"error", "code_rejected"} else "next"

    graph.add_conditional_edges("ingest", route_after_validation, {"invalid_request": "invalid_request", "next": "llm_analysis"})
    graph.add_conditional_edges("llm_analysis", route_after_llm_step, {"execution_error": "execution_error", "next": "code_generation"})
    graph.add_conditional_edges("code_generation", route_after_llm_step, {"execution_error": "execution_error", "next": "code_security"})
    graph.add_conditional_edges("code_security", route_after_security, {"execution_error": "execution_error", "next": "code_execution"})
    graph.add_conditional_edges("code_execution", route_after_execution, {"execution_error": "execution_error", "interpretation": "interpretation"})
    graph.add_edge("interpretation", END)
    graph.add_edge("invalid_request", END)
    graph.add_edge("execution_error", END)
    compiled = graph.compile()

    class LangGraphAdapter(SimpleFinancialWorkflow):
        def invoke(self, query_input: FinancialQueryInput) -> WorkflowState:
            initial = WorkflowState.from_input(query_input)
            result = compiled.invoke(initial)
            if isinstance(result, WorkflowState):
                return result
            return replace(initial, **result)

    return LangGraphAdapter()
