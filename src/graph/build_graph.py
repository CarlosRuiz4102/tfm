from __future__ import annotations

from typing import Callable

from src.graph.nodes import (
    code_execution_node,
    code_generation_node,
    code_security_node,
    data_download_node,
    data_request_planning_node,
    data_request_structural_validation_node,
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
        # El pipeline refleja el orden del flujo nuevo: primero resolvemos datos,
        # luego analizamos, generamos código, validamos, ejecutamos e interpretamos.
        self.pipeline: list[NodeFn] = [
            ingest_node,
            data_request_planning_node,
            data_request_structural_validation_node,
            data_download_node,
            llm_analysis_node,
            code_generation_node,
            code_security_node,
            code_execution_node,
            interpretation_node,
        ]

    def invoke(self, query_input: FinancialQueryInput) -> WorkflowState:
        # invoke recorre el pipeline y decide en qué tipos de estado terminal
        # debe cortar la ejecución sin seguir al siguiente nodo.
        state = WorkflowState.from_input(query_input)
        for node in self.pipeline:
            state = node(state)
            if state.status == "invalid":
                return invalid_request_node(state)
            if state.status == "blocked":
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
