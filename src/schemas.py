from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FinancialQueryInput:
    """Entrada mínima que captura la query del usuario y sirve de entrada al workflow."""

    # La nueva arquitectura parte de una idea simple: la entrada inicial solo
    # representa lo que escribe el usuario. Todo lo técnico se resuelve más
    # adelante en el FinancialDataRequest.
    query: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialQueryInput":
        # Ignoramos el resto de claves para que esta clase no absorba campos
        # que pertenecen a fases posteriores del flujo.
        return cls(query=str(data.get("query") or ""))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InstrumentRequest:
    """Representa un instrumento financiero ya resuelto a ticker."""

    # Se mantiene como objeto propio para poder ampliar el contrato en el
    # futuro sin romper el resto del workflow.
    ticker: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstrumentRequest":
        return cls(ticker=str(data.get("ticker") or "").strip())

    def to_dict(self) -> dict[str, str]:
        return {"ticker": self.ticker}


@dataclass
class FinancialDataRequest:
    """
    Contrato central de la fase de datos que genera el agente 1

    Resume qué instrumentos, rango temporal y granularidad deben usarse para descargar la información en yfinance.
    """

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
        # Aquí forzamos una forma interna estable del request, aunque el JSON
        # del LLM venga con pequeñas variaciones de formato.
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
        """Atajo útil para las capas que solo necesitan la lista de tickers."""
        return [instrument.ticker for instrument in self.instruments if instrument.ticker]

    def to_dict(self) -> dict[str, Any]:
        # El workflow y los artefactos persistidos trabajan mejor con dicts
        # planos serializables que con dataclasses anidadas.
        payload = asdict(self)
        payload["instruments"] = [instrument.to_dict() for instrument in self.instruments]
        return payload


@dataclass
class DataDownloadArtifacts:
    """Rutas a los artefactos persistidos que deja la descarga."""

    # Conservamos por separado request, bruto, normalizado y metadata para poder
    # reconstruir qué se pidió, qué devolvió la API y qué consumió el sistema.
    request_path: str
    raw_data_path: str
    normalized_data_path: str
    metadata_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DataDownloadSummary:
    """Resumen ligero de la descarga listo para pasar al siguiente agente."""

    # Este resumen evita que el siguiente agente tenga que abrir ficheros solo
    # para averiguar qué se descargó y con qué cobertura básica.
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


@dataclass
class AnalysisPlan:
    """Plan analítico que consume la fase de generación de código."""

    # A partir de aquí el sistema deja de resolver qué datos hacen falta y pasa
    # a decidir qué cálculos deben hacerse sobre esos datos ya descargados.
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
    """Contenedor previsto para futuras salidas más ricas del generador."""

    # De momento el pipeline usa sobre todo el campo code, pero dejamos esta
    # estructura para futuras ampliaciones del contrato de generación.
    code: str
    expected_outputs: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionArtifacts:
    """Rutas a los ficheros generados durante la ejecución del script."""

    # Estas rutas permiten auditar el comportamiento del script generado sin
    # depender solo de la respuesta final del flujo.
    script_path: str
    payload_path: str
    stdout_path: str
    stderr_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    """Resultado bruto y parseado de la ejecución del código generado."""

    # parsed_output es la versión estructurada de stdout cuando el script cumple
    # el contrato y devuelve JSON utilizable.
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
    """
    Estado compartido del workflow. De aqui lo interesante es ver en que estado nos encontramos en cada parte del flow

    "Revisar al final del todo si es necesario cada campo"

    Cada nodo lee una parte, añade artefactos o resultados nuevos y actualiza el campo status para indicar en qué etapa se encuentra el flujo.
    """

    user_query: str
    normalized_query: dict[str, Any]
    csv_paths: list[str]
    # financial_data_request, download_artifacts y download_summary son la
    # memoria explícita de la nueva fase de datos.
    financial_data_request: dict[str, Any] | None = None
    download_artifacts: dict[str, Any] | None = None
    download_summary: dict[str, Any] | None = None
    # analysis_plan y generated_code pertenecen ya a la fase analítica y de
    # codegen del sistema.
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
    # Contadores independientes para distinguir si se ha agotado la reparación
    # estructural o la operativa.
    structural_repair_attempts: int = 0
    operational_repair_attempts: int = 0

    @classmethod
    def from_input(cls, query_input: FinancialQueryInput) -> "WorkflowState":
        return cls(
            user_query=query_input.query,
            normalized_query=query_input.to_dict(),
            csv_paths=[],
            warnings=[],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
