from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from src.config import RESULTS_TRACES_DIR


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid4().hex[:8]


def _state_summary(state) -> dict[str, Any]:
    """
    Resume el estado para los eventos de traza sin volcar siempre todo el objeto.

    Los snapshots completos se escriben aparte. En los eventos interesa un
    resumen ligero para localizar rapido donde fallo una ejecucion.
    """
    return {
        "status": state.status,
        "error_message": state.error_message,
        "warnings_count": len(state.warnings),
        "structural_repair_attempts": state.structural_repair_attempts,
        "operational_repair_attempts": state.operational_repair_attempts,
        "code_repair_attempts": state.code_repair_attempts,
        "execution_attempts": state.execution_attempts,
        "execution_repair_attempts": state.execution_repair_attempts,
        "has_financial_data_request": state.financial_data_request is not None,
        "has_generated_code": state.generated_code is not None,
        "has_execution_output": state.execution_output is not None,
        "has_interpretation_payload": state.interpretation_payload is not None,
        "has_final_answer": bool(state.final_answer.strip()),
    }


def _artifact_summary(state) -> dict[str, Any]:
    return {
        "csv_paths": list(state.csv_paths),
        "download_artifacts": state.download_artifacts.to_dict() if state.download_artifacts else None,
        "execution_artifacts": state.execution_artifacts.to_dict() if state.execution_artifacts else None,
        "trace_dir": state.trace_dir,
    }


@dataclass
class WorkflowTraceRecorder:
    """
    Traza estructurada de una ejecucion completa del workflow.

    Se ha pensado para depurar ejemplos reales del proyecto sin depender de
    logs dispersos ni de inspeccionar manualmente el `final_answer`.
    """

    run_id: str
    trace_dir: Path
    events_path: Path
    manifest_path: Path
    snapshots_dir: Path

    def _append_event(self, event: dict[str, Any]) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_event(self, event_type: str, **payload: Any) -> None:
        event = {
            "run_id": self.run_id,
            "timestamp": _now_iso(),
            "event_type": event_type,
        }
        event.update(payload)
        self._append_event(event)

    def write_snapshot(self, label: str, state) -> None:
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.snapshots_dir / f"{label}.json"
        snapshot_path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.log_event(
            "state_snapshot_written",
            label=label,
            snapshot_path=str(snapshot_path),
        )

    def write_manifest(self, state, node_order: list[str], started_at: str, finished_at: str | None = None) -> None:
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "run_id": self.run_id,
            "query": state.user_query,
            "started_at": started_at,
            "finished_at": finished_at,
            "current_status": state.status,
            "trace_dir": str(self.trace_dir),
            "events_path": str(self.events_path),
            "snapshots_dir": str(self.snapshots_dir),
            "node_order": node_order,
            "artifacts": _artifact_summary(state),
        }
        self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def trace_node(self, node_name: str, state, node_call) -> Any:
        status_before = state.status
        self.log_event(
            "node_started",
            node_name=node_name,
            status_before=status_before,
            state_summary=_state_summary(state),
        )
        started = perf_counter()
        new_state = node_call(state)
        duration_ms = round((perf_counter() - started) * 1000, 3)
        self.log_event(
            "node_completed",
            node_name=node_name,
            status_before=status_before,
            status_after=new_state.status,
            duration_ms=duration_ms,
            state_summary=_state_summary(new_state),
            artifacts=_artifact_summary(new_state),
        )
        return new_state


def create_workflow_trace_recorder(query: str) -> WorkflowTraceRecorder:
    run_id = _new_run_id()
    trace_dir = RESULTS_TRACES_DIR / run_id
    trace_dir.mkdir(parents=True, exist_ok=True)
    return WorkflowTraceRecorder(
        run_id=run_id,
        trace_dir=trace_dir,
        events_path=trace_dir / "events.jsonl",
        manifest_path=trace_dir / "manifest.json",
        snapshots_dir=trace_dir / "snapshots",
    )
