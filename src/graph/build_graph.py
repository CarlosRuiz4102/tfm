from __future__ import annotations

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
    return SimpleFinancialWorkflow()
