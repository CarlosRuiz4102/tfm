from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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
    returncode: int
    parsed_output: dict[str, Any] | None
    artifacts: ExecutionArtifacts

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = self.artifacts.to_dict()
        return payload

