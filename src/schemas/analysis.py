from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TemporalContext:
    """Contexto temporal compacto que se pasa a la fase 2."""

    start: str | None = None
    end: str | None = None
    period: str | None = None
    interval: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Phase2DataContext:
    """Resumen minimo de los datos reales que necesita el LLM en la parte 2."""

    row_count: int | None = None
    available_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Phase2PromptContext:
    """
    Payload compacto que conecta la fase de datos con analista y codegen.

    Mantiene lo necesario para el LLM sin arrastrar toda la trazabilidad
    detallada del workflow.
    """

    query: str
    tickers: list[str]
    temporal_context: TemporalContext
    csv_paths: list[str]
    data_context: Phase2DataContext
    warnings: list[str] = field(default_factory=list)
    download_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisPlan:
    """Plan analitico que consume la fase de generacion de codigo."""

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
