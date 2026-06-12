from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FinancialQueryInput:
    query: str
    tickers: list[str]
    csv_paths: list[str]
    start: str | None = None
    end: str | None = None
    period: str | None = None
    interval: str | None = None
    needs_clarification: bool = False
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialQueryInput":
        warnings = data.get("warnings") or []
        if isinstance(warnings, str):
            warnings = [warnings] if warnings else []
        return cls(
            query=data["query"],
            tickers=list(data.get("tickers") or []),
            csv_paths=[str(path) for path in data.get("csv_paths") or []],
            start=data.get("start"),
            end=data.get("end"),
            period=data.get("period"),
            interval=data.get("interval"),
            needs_clarification=bool(data.get("needs_clarification", False)),
            warnings=warnings,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisPlan:
    analytical_goal: str
    analysis_type: str
    metrics: list[str]
    required_columns: list[str]
    data_requirements: list[str]
    output_requirements: list[str]
    presentation_preferences: list[str]
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodeGenOutput:
    code: str
    expected_outputs: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionArtifacts:
    script_path: str
    payload_path: str
    stdout_path: str
    stderr_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    returncode: int
    parsed_output: dict[str, Any] | None
    artifacts: ExecutionArtifacts

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = self.artifacts.to_dict()
        return payload


@dataclass
class WorkflowState:
    user_query: str
    normalized_query: dict[str, Any]
    csv_paths: list[str]
    analysis_plan: dict[str, Any] | None = None
    generated_code: str | None = None
    execution_stdout: str = ""
    execution_stderr: str = ""
    execution_returncode: int | None = None
    execution_output: dict[str, Any] | None = None
    execution_artifacts: dict[str, Any] | None = None
    final_answer: str = ""
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None
    status: str = "created"

    @classmethod
    def from_input(cls, query_input: FinancialQueryInput) -> "WorkflowState":
        return cls(
            user_query=query_input.query,
            normalized_query=query_input.to_dict(),
            csv_paths=list(query_input.csv_paths),
            warnings=list(query_input.warnings),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
