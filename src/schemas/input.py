from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FinancialQueryInput:
    """Entrada minima con la consulta libre del usuario."""

    query: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialQueryInput":
        return cls(query=str(data.get("query") or ""))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResolvedQueryContext:
    """
    Contexto resuelto que va enriqueciendose a lo largo del workflow.

    Esta estructura sustituye al antiguo `normalized_query` generico para dejar
    claro que aqui guardamos la query original mas los campos que la fase de
    datos va resolviendo de forma progresiva.
    """

    query: str
    tickers: list[str] = field(default_factory=list)
    start: str | None = None
    end: str | None = None
    period: str | None = None
    interval: str | None = None
    needs_clarification: bool = False
    csv_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_query_input(cls, query_input: FinancialQueryInput) -> "ResolvedQueryContext":
        return cls(query=query_input.query)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResolvedQueryContext":
        return cls(
            query=str(data.get("query") or ""),
            tickers=[str(item) for item in data.get("tickers") or [] if str(item).strip()],
            start=data.get("start"),
            end=data.get("end"),
            period=data.get("period"),
            interval=data.get("interval"),
            needs_clarification=bool(data.get("needs_clarification", False)),
            csv_paths=[str(item) for item in data.get("csv_paths") or [] if str(item).strip()],
            warnings=[str(item) for item in data.get("warnings") or [] if str(item).strip()],
        )

    def to_query_input(self) -> FinancialQueryInput:
        return FinancialQueryInput(query=self.query)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

