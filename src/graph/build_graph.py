from __future__ import annotations

from datetime import datetime
from typing import Callable

from src.graph.nodes import (
    code_execution_node,
    code_generation_node,
    code_validation_node,
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
from src.tracing import create_workflow_trace_recorder


NodeFn = Callable[[WorkflowState], WorkflowState]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class SimpleFinancialWorkflow:
    def __init__(self) -> None:
        # El pipeline refleja el orden del flujo nuevo: primero resolvemos datos,
        # luego analizamos, generamos codigo, validamos, ejecutamos e interpretamos.
        self.pipeline: list[NodeFn] = [
            ingest_node,
            data_request_planning_node,
            data_request_structural_validation_node,
            data_download_node,
            llm_analysis_node,
            code_generation_node,
            code_validation_node,
            code_execution_node,
            interpretation_node,
        ]
        # Algunos estados terminales no salen directamente al usuario: pasan
        # antes por un nodo final que convierte el bloqueo o error en una salida
        # final coherente y trazable.
        self.terminal_handlers: dict[str, tuple[str, NodeFn]] = {
            "invalid": ("invalid_request_node", invalid_request_node),
            "blocked": ("invalid_request_node", invalid_request_node),
            "error": ("execution_error_node", execution_error_node),
            "code_rejected": ("execution_error_node", execution_error_node),
            "execution_failed": ("execution_error_node", execution_error_node),
        }

    def invoke(self, query_input: FinancialQueryInput) -> WorkflowState:
        # invoke recorre el pipeline y, ademas, deja una traza estructurada
        # completa para poder depurar ejecuciones reales ejemplo a ejemplo.
        state = WorkflowState.from_input(query_input)
        recorder = create_workflow_trace_recorder(query_input.query)
        started_at = _now_iso()
        node_order = [node.__name__ for node in self.pipeline]

        state.run_id = recorder.run_id
        state.trace_dir = str(recorder.trace_dir)

        recorder.write_manifest(state, node_order=node_order, started_at=started_at)
        recorder.log_event(
            "workflow_started",
            query=query_input.query,
            state_summary={"status": state.status},
        )
        recorder.write_snapshot("00_initial_state", state)

        for index, node in enumerate(self.pipeline, start=1):
            state = recorder.trace_node(node.__name__, state, node)
            recorder.write_snapshot(f"{index:02d}_{node.__name__}", state)

            terminal_handler = self.terminal_handlers.get(state.status)
            if terminal_handler is not None:
                terminal_name, terminal_node = terminal_handler
                state = recorder.trace_node(terminal_name, state, terminal_node)
                recorder.write_snapshot(f"{index:02d}_terminal_{terminal_name}", state)
                recorder.log_event("workflow_finished", final_status=state.status)
                recorder.write_manifest(state, node_order=node_order, started_at=started_at, finished_at=_now_iso())
                return state

        recorder.log_event("workflow_finished", final_status=state.status)
        recorder.write_manifest(state, node_order=node_order, started_at=started_at, finished_at=_now_iso())
        return state


def build_workflow() -> SimpleFinancialWorkflow:
    return SimpleFinancialWorkflow()
