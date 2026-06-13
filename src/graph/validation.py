from __future__ import annotations

from src.data.validation import validate_query_input
from src.schemas import FinancialQueryInput


def validate_input(query_input: FinancialQueryInput) -> list[str]:
    """Puerta de entrada común del workflow para validar la consulta original."""
    # Mantenemos esta función como fachada para que el grafo no dependa
    # directamente de la ubicación interna de la validación de entrada.
    return validate_query_input(query_input)
