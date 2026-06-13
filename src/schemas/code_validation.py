from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_CODE_VALIDATION_DECISIONS = {"valid", "repairable", "blocked"}


@dataclass
class CodeValidationDecision:
    """
    Decision estructurada del Agente 4 sobre el codigo generado.

    Este objeto actua como contrato entre el validador, el subagente de
    correccion y el resto del workflow.
    """

    decision: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_fixes: list[str] = field(default_factory=list)
    reasoning: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CodeValidationDecision":
        decision = str(payload.get("decision") or "").strip().lower()
        if decision not in ALLOWED_CODE_VALIDATION_DECISIONS:
            raise ValueError(
                "decision debe ser una de: "
                + ", ".join(sorted(ALLOWED_CODE_VALIDATION_DECISIONS))
            )

        reasoning = str(payload.get("reasoning") or "").strip()
        if not reasoning:
            raise ValueError("reasoning no puede estar vacio.")

        return cls(
            decision=decision,
            errors=_as_clean_str_list(payload.get("errors")),
            warnings=_as_clean_str_list(payload.get("warnings")),
            required_fixes=_as_clean_str_list(payload.get("required_fixes")),
            reasoning=reasoning,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_clean_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
