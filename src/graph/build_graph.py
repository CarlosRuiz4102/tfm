from __future__ import annotations

from dataclasses import replace
from typing import Callable

from src.graph.nodes import (
    code_execution_node,
    code_generation_node,
    execution_error_node,
    ingest_node,
    interpretation_node,
    invalid_request_node,
    orchestrator_router_node,
    specialist_analysis_node,
)
from src.schemas import FinancialQueryInput, WorkflowState


NodeFn = Callable[[WorkflowState], WorkflowState]


class SimpleFinancialWorkflow:
    def __init__(self) -> None:
        self.pipeline: list[NodeFn] = [
            ingest_node,
            orchestrator_router_node,
            specialist_analysis_node,
            code_generation_node,
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
    graph.add_node("router", orchestrator_router_node)
    graph.add_node("specialist_analysis", specialist_analysis_node)
    graph.add_node("code_generation", code_generation_node)
    graph.add_node("code_execution", code_execution_node)
    graph.add_node("interpretation", interpretation_node)
    graph.add_node("invalid_request", invalid_request_node)
    graph.add_node("execution_error", execution_error_node)

    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "router")

    def route_after_router(state: WorkflowState) -> str:
        return "invalid_request" if state.status == "invalid" else "specialist_analysis"

    def route_after_execution(state: WorkflowState) -> str:
        return "execution_error" if state.execution_returncode else "interpretation"

    graph.add_conditional_edges("router", route_after_router, {"invalid_request": "invalid_request", "specialist_analysis": "specialist_analysis"})
    graph.add_edge("specialist_analysis", "code_generation")
    graph.add_edge("code_generation", "code_execution")
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
