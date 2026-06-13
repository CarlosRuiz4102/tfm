from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.schemas.analysis import AnalysisPlan
from src.schemas.data import DataDownloadArtifacts, DataDownloadSummary, FinancialDataRequest
from src.schemas.execution import ExecutionArtifacts
from src.schemas.input import FinancialQueryInput, ResolvedQueryContext


@dataclass
class WorkflowState:
    """
    Estado compartido del workflow.

    Mantiene un unico objeto de trabajo, pero con tipos explicitos para que el
    flujo no dependa de dicts genericos en cada fase.
    """

    user_query: str
    normalized_query: ResolvedQueryContext
    csv_paths: list[str]
    financial_data_request: FinancialDataRequest | None = None
    download_artifacts: DataDownloadArtifacts | None = None
    download_summary: DataDownloadSummary | None = None
    analysis_plan: AnalysisPlan | None = None
    generated_code: str | None = None
    execution_stdout: str = ""
    execution_stderr: str = ""
    execution_returncode: int | None = None
    execution_output: dict[str, Any] | None = None
    execution_artifacts: ExecutionArtifacts | None = None
    final_answer: str = ""
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None
    status: str = "created"
    structural_repair_attempts: int = 0
    operational_repair_attempts: int = 0

    @classmethod
    def from_input(cls, query_input: FinancialQueryInput) -> "WorkflowState":
        return cls(
            user_query=query_input.query,
            normalized_query=ResolvedQueryContext.from_query_input(query_input),
            csv_paths=[],
            warnings=[],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
