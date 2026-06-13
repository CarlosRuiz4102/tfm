from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class InstrumentRequest:
    """Representa un instrumento financiero ya resuelto a ticker."""

    ticker: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstrumentRequest":
        return cls(ticker=str(data.get("ticker") or "").strip())

    def to_dict(self) -> dict[str, str]:
        return {"ticker": self.ticker}


@dataclass
class FinancialDataRequest:
    """Contrato de datos que sale del Agente 1 y consume la fase de descarga."""

    user_query: str
    provider: str
    instruments: list[InstrumentRequest]
    interval: str
    start: str | None = None
    end: str | None = None
    period: str | None = None
    required_fields: list[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_reason: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialDataRequest":
        instruments = data.get("instruments") or []
        return cls(
            user_query=str(data.get("user_query") or ""),
            provider=str(data.get("provider") or ""),
            instruments=[
                item if isinstance(item, InstrumentRequest) else InstrumentRequest.from_dict(item)
                for item in instruments
            ],
            interval=str(data.get("interval") or ""),
            start=data.get("start"),
            end=data.get("end"),
            period=data.get("period"),
            required_fields=[str(field_name) for field_name in data.get("required_fields") or []],
            needs_clarification=bool(data.get("needs_clarification", False)),
            clarification_reason=(
                str(data.get("clarification_reason")).strip()
                if data.get("clarification_reason") is not None
                else None
            ),
        )

    @property
    def tickers(self) -> list[str]:
        return [instrument.ticker for instrument in self.instruments if instrument.ticker]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["instruments"] = [instrument.to_dict() for instrument in self.instruments]
        return payload


@dataclass
class DataDownloadArtifacts:
    """Rutas a los artefactos persistidos que deja la descarga."""

    request_path: str
    raw_data_path: str
    normalized_data_path: str
    metadata_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DataDownloadSummary:
    """Resumen ligero de la descarga real ya normalizada."""

    provider: str
    tickers_requested: list[str]
    tickers_found: list[str]
    interval: str
    period: str | None
    start: str | None
    end: str | None
    row_count: int
    columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

