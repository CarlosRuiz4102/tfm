from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_EXECUTION_VALIDATION_DECISIONS = {"valid", "repairable", "blocked"}


@dataclass
class ExecutionArtifacts:
    """Rutas a los ficheros generados durante la ejecucion del script."""

    script_path: str
    payload_path: str
    stdout_path: str
    stderr_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    """Resultado bruto y parseado de la ejecucion del codigo generado."""

    stdout: str
    stderr: str
    returncode: int | None
    parsed_output: Any | None
    artifacts: ExecutionArtifacts
    timed_out: bool = False
    launch_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = self.artifacts.to_dict()
        return payload


@dataclass
class ExecutionValidationDecision:
    """
    Decision estructurada de la parte 4 sobre un intento de ejecucion.

    A diferencia del Agente 4, aqui no se valida codigo "en frio". Se valida
    la evidencia observable que deja el intento real de ejecucion.
    """

    decision: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reasoning: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExecutionValidationDecision":
        decision = str(payload.get("decision") or "").strip().lower()
        if decision not in ALLOWED_EXECUTION_VALIDATION_DECISIONS:
            raise ValueError(
                "decision debe ser una de: "
                + ", ".join(sorted(ALLOWED_EXECUTION_VALIDATION_DECISIONS))
            )

        reasoning = str(payload.get("reasoning") or "").strip()
        if not reasoning:
            raise ValueError("reasoning no puede estar vacio.")

        return cls(
            decision=decision,
            errors=_as_clean_str_list(payload.get("errors")),
            warnings=_as_clean_str_list(payload.get("warnings")),
            reasoning=reasoning,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_clean_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
