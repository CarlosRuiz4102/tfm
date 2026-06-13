from __future__ import annotations

from dataclasses import dataclass, field

from src.schemas import AnalysisPlan


ALLOWED_ANALYSIS_TYPES = {
    "historical_overview",
    "historical_return_analysis",
    "comparative_return_analysis",
    "volatility_analysis",
    "drawdown_analysis",
    "technical_indicator_analysis",
    "risk_return_profile",
}


@dataclass
class AnalysisPlanValidationResult:
    """Resultado simple para inspeccionar si el plan es utilizable o no."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_analysis_plan(
    plan: AnalysisPlan,
    *,
    available_columns: list[str] | None = None,
) -> AnalysisPlanValidationResult:
    """
    Comprueba que el AnalysisPlan tenga una forma estable antes del codegen.

    Esta capa hace en la parte analitica lo mismo que la validacion estructural hace en la fase de datos: revisar 
    localmente el contrato del LLM antes de permitir que el flujo siga avanzando.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not plan.analytical_goal.strip():
        errors.append("analytical_goal no puede estar vacio.")

    if plan.analysis_type not in ALLOWED_ANALYSIS_TYPES:
        errors.append(
            "analysis_type no permitido. Valores esperados: "
            + ", ".join(sorted(ALLOWED_ANALYSIS_TYPES))
        )

    if not plan.metrics:
        errors.append("metrics debe contener al menos una metrica.")
    elif len(plan.metrics) != len(set(plan.metrics)):
        warnings.append("metrics contiene valores duplicados.")

    if not plan.required_columns:
        errors.append("required_columns debe contener al menos una columna.")

    if available_columns:
        unknown_columns = [column for column in plan.required_columns if column not in available_columns]
        if unknown_columns:
            errors.append(
                "required_columns contiene columnas que no aparecen en la descarga normalizada: "
                + ", ".join(unknown_columns)
            )

    if not plan.data_requirements:
        errors.append("data_requirements debe describir al menos una restriccion de datos.")

    if not plan.output_requirements:
        errors.append("output_requirements debe describir la salida esperada del script.")
    else:
        output_text = " ".join(plan.output_requirements).lower()
        if "json" not in output_text:
            warnings.append("output_requirements no menciona explicitamente una salida JSON.")

    if not plan.presentation_preferences:
        errors.append("presentation_preferences debe contener al menos una preferencia de presentacion.")

    if not plan.reasoning.strip():
        errors.append("reasoning no puede estar vacio.")

    return AnalysisPlanValidationResult(is_valid=not errors, errors=errors, warnings=warnings)
