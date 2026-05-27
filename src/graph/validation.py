from __future__ import annotations

from datetime import date

from src.io.csv_loader import csv_exists
from src.schemas import FinancialQueryInput


def _is_iso_date(value: str | None) -> bool:
    if not value:
        return True
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_input(query_input: FinancialQueryInput) -> list[str]:
    errors: list[str] = []
    if not query_input.query.strip():
        errors.append("La query no puede estar vacia.")
    if not query_input.tickers:
        errors.append("Debe existir al menos un ticker.")
    if not query_input.csv_paths:
        errors.append("Debe existir al menos una ruta CSV.")
    if not _is_iso_date(query_input.start):
        errors.append("La fecha start debe tener formato YYYY-MM-DD.")
    if not _is_iso_date(query_input.end):
        errors.append("La fecha end debe tener formato YYYY-MM-DD.")
    for csv_path in query_input.csv_paths:
        if not csv_exists(csv_path):
            errors.append(f"No existe el CSV: {csv_path}")
    return errors
