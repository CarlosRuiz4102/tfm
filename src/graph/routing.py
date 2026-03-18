from __future__ import annotations

from src.io.csv_loader import csv_exists
from src.schemas import FinancialQueryInput, RouterOutput, SUPPORTED_INTENTS


def validate_input(query_input: FinancialQueryInput) -> list[str]:
    errors: list[str] = []
    if not query_input.query.strip():
        errors.append("La query no puede estar vacia.")
    if query_input.intent not in SUPPORTED_INTENTS:
        errors.append(f"La intent '{query_input.intent}' no esta soportada en este MVP.")
    if not query_input.tickers:
        errors.append("Debe existir al menos un ticker.")
    if not query_input.csv_paths:
        errors.append("Debe existir al menos una ruta CSV.")
    for csv_path in query_input.csv_paths:
        if not csv_exists(csv_path):
            errors.append(f"No existe el CSV: {csv_path}")
    return errors


def route_intent(query_input: FinancialQueryInput) -> RouterOutput:
    errors = validate_input(query_input)
    if errors:
        return RouterOutput(
            selected_agent="invalid_request_node",
            is_valid=False,
            warnings=[],
            error_message=" | ".join(errors),
        )

    if query_input.intent == "price_growth" and len(query_input.tickers) != 1:
        return RouterOutput(
            selected_agent="invalid_request_node",
            is_valid=False,
            error_message="price_growth requiere exactamente 1 ticker.",
        )

    if query_input.intent == "compare_assets" and len(query_input.tickers) < 2:
        return RouterOutput(
            selected_agent="invalid_request_node",
            is_valid=False,
            error_message="compare_assets requiere al menos 2 tickers.",
        )

    selected_agent = "growth_agent" if query_input.intent == "price_growth" else "compare_agent"
    return RouterOutput(
        selected_agent=selected_agent,
        is_valid=True,
        warnings=list(query_input.warnings),
    )
