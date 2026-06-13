from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from src.schemas import FinancialDataRequest, FinancialQueryInput


ALLOWED_PROVIDER = "yfinance"
ALLOWED_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}
NORMALIZED_REQUIRED_COLUMNS = {"Date", "Ticker", "Close"}


@dataclass
class ValidationDecision:
    """Salida común de las validaciones de esta fase: continuar, reparar o bloquear."""

    # status usa la semántica acordada en la guía:
    # valid -> continuar
    # repairable -> intentar corrección
    # blocked -> detener la ejecución actual de esta fase
    status: str
    errors: list[str] = field(default_factory=list)


def _is_iso_date(value: str | None) -> bool:
    # Este helper solo comprueba formato. No decide si una fecha es obligatoria
    # o no; esa responsabilidad pertenece a la validacion estructural.
    if not value:
        return True
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_query_input(query_input: FinancialQueryInput) -> list[str]:
    """Validación mínima de la consulta original antes de entrar en la fase LLM."""
    # Esta validacion se ejecuta en ingest_node.
    #
    # Aqui aun no existe FinancialDataRequest, no hay provider, no hay
    # instrumentos resueltos ni tampoco sabemos si la descarga funcionara.
    # Por eso solo validamos la unica promesa real de FinancialQueryInput:
    # que el usuario haya escrito una consulta no vacia.
    #
    # Si falla aqui, el flujo ni siquiera llega al Agente 1.
    errors: list[str] = []
    if not query_input.query.strip():
        errors.append("La query no puede estar vacia.")
    return errors


def validate_financial_data_request_structure(request: FinancialDataRequest) -> ValidationDecision:
    """
    Comprueba si el FinancialDataRequest está bien construido antes de tocar yfinance.

    Esta es la validación "formal": campos, fechas, intervalos y coherencia interna del contrato de datos.

    Se ejecuta justo despues de que el Agente 1 genere el request, y tambien
    despues de cada intento de correccion estructural del Subagente 1.

    Lo importante aqui es que todavia no se descarga nada. Solo se decide  si el request 
    "tiene forma correcta" para merecer una prueba real contra yfinance.
    """
    if request.needs_clarification:
        # Si el propio request reconoce que faltan datos críticos, no intentamos
        # "arreglarlo" forzando supuestos: se bloquea de forma explícita.
        #
        # Este caso corresponde a consultas donde el sistema no deberia inventar
        # ticker, rango o granularidad sin una pista fiable del usuario.
        reason = request.clarification_reason or "La consulta requiere aclaracion adicional."
        return ValidationDecision(status="blocked", errors=[reason])

    errors: list[str] = []
    # 1. El request debe conservar la consulta original para mantener trazabilidad
    # entre lo que el usuario pidio y lo que el sistema va a descargar.
    if not request.user_query.strip():
        errors.append("El request debe conservar la consulta original.")
    # 2. El provider debe existir y debe ser uno soportado por esta version del sistema.
    if not request.provider.strip():
        errors.append("Debe indicarse un provider.")
    elif request.provider != ALLOWED_PROVIDER:
        errors.append(f"Provider no soportado: {request.provider}")
    # 3. Debe haber al menos un instrumento y cada instrumento debe llegar
    # resuelto a ticker. Aqui no aceptamos nombres vagos o elementos vacios.
    if not request.instruments:
        errors.append("Debe existir al menos un instrumento.")
    else:
        empty_tickers = [instrument.ticker for instrument in request.instruments if not instrument.ticker.strip()]
        if empty_tickers:
            errors.append("Todos los instrumentos deben incluir ticker.")

    # 4. El intervalo debe pertenecer a una lista de granularidades que sabemos
    # que son compatibles con el proveedor previsto.
    if not request.interval.strip():
        errors.append("Debe indicarse un interval.")
    elif request.interval not in ALLOWED_INTERVALS:
        errors.append(f"El intervalo {request.interval} no pertenece a la lista permitida.")

    # 5. El rango temporal debe ser coherente:
    # - o bien usamos "period"
    # - o bien usamos "start" y opcionalmente "end"
    # pero no mezclamos ambas estrategias a la vez.
    if request.period and (request.start or request.end):
        errors.append("No deben coexistir period y start/end en el mismo request.")
    if not request.period and not request.start:
        errors.append("Debe existir period o start.")
    # 6. Si hay fechas explicitas, deben venir en formato ISO y en orden lógico.
    if not _is_iso_date(request.start):
        errors.append("La fecha start del request debe tener formato YYYY-MM-DD.")
    if not _is_iso_date(request.end):
        errors.append("La fecha end del request debe tener formato YYYY-MM-DD.")
    if request.start and request.end and request.end < request.start:
        errors.append("La fecha end debe ser posterior o igual a start.")

    if errors:
        # Aquí todavía estamos en terreno corregible: el request puede venir mal
        # formado aunque la intención original del usuario siga siendo utilizable.
        #
        # Ejemplos tipicos:
        # - intervalo no permitido
        # - falta ticker
        # - mezcla de period con start/end
        # - fechas mal formadas
        #
        # En esos casos entra el Subagente 1.
        return ValidationDecision(status="repairable", errors=errors)
    # Si llega aqui, el request esta formalmente listo para pasar a la descarga real.
    return ValidationDecision(status="valid")


def validate_operational_download(
    request: FinancialDataRequest,
    normalized_data: pd.DataFrame,
) -> ValidationDecision:
    """
    Comprueba si la descarga real ha producido datos útiles.

    Aquí ya no validamos el request en abstracto, sino el resultado de haber intentado descargarlo y normalizarlo.

    Se ejecuta dentro de data_download_node, despues de:
    1. llamar a yfinance,
    2. normalizar la respuesta a un dataframe tabular comun,
    3. comprobar si ese dataframe realmente sirve como entrada del resto del flujo.

    Esta funcion responde a la pregunta:
    "Aunque el request estaba bien construido, ¿la descarga real ha salido bien?"
    """
    errors: list[str] = []
    if normalized_data.empty:
        # Descargar y obtener cero filas suele indicar que la combinación de
        # ticker/rango/intervalo no ha funcionado operativamente.
        #
        # Este es el caso clasico de "la estructura parecia valida pero la
        # operativa real no produjo datos utiles".
        errors.append("La descarga no devolvio filas utilizables.")
        return ValidationDecision(status="repairable", errors=errors)

    # 1. El dataframe normalizado debe contener las columnas minimas que el
    # resto del sistema espera para seguir trabajando.
    missing_columns = sorted(NORMALIZED_REQUIRED_COLUMNS.difference(normalized_data.columns))
    if missing_columns:
        errors.append(f"Faltan columnas minimas en la descarga normalizada: {', '.join(missing_columns)}.")

    # 2. Deben aparecer realmente los tickers que se pidieron. Asi evitamos
    # continuar con una descarga parcial o con un ticker incorrecto.
    tickers_found = sorted({str(ticker).strip() for ticker in normalized_data.get("Ticker", []) if str(ticker).strip()})
    missing_tickers = sorted(set(request.tickers).difference(tickers_found))
    if missing_tickers:
        errors.append(f"No aparecieron todos los tickers solicitados: {', '.join(missing_tickers)}.")

    # 3. Close debe contener valores reales porque es la columna minima sobre
    # la que luego se apoyan analisis y scripts posteriores.
    if "Close" in normalized_data.columns and normalized_data["Close"].dropna().empty:
        errors.append("La descarga no contiene valores validos en Close.")

    if errors:
        # Si el request parecía válido pero la descarga no sirve, el problema ya
        # pertenece a la ruta operativa de corrección.
        #
        # En esos casos entra el Subagente 2, que ya no corrige "forma", sino
        # viabilidad operativa de la descarga.
        return ValidationDecision(status="repairable", errors=errors)
    # Si llega aqui, la fase de datos ya puede entregar artefactos fiables al Agente 2.
    return ValidationDecision(status="valid")
