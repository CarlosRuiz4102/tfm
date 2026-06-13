from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.config import (
    RESULTS_DATA_NORMALIZED_DIR,
    RESULTS_DATA_RAW_DIR,
    RESULTS_DATA_REQUESTS_DIR,
)
from src.schemas import DataDownloadArtifacts, DataDownloadSummary, FinancialDataRequest


PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def download_market_data(request: FinancialDataRequest) -> pd.DataFrame:
    """Ejecuta la descarga real en yfinance con el request ya validado."""
    # No hacemos aquí lógica de corrección: este bloque asume que el request ya
    # pasó la validación estructural y se limita a probar la descarga real.
    return yf.download(
        tickers=request.tickers,
        start=request.start,
        end=request.end,
        period=request.period,
        interval=request.interval,
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=False,
    )


def normalize_downloaded_data(downloaded: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """
    Convierte la salida de yfinance a un formato canónico largo.

    El resto del sistema trabaja mejor con columnas explícitas:
    Date, Ticker, Open, High, Low, Close, Adj Close y Volume.
    """
    if downloaded.empty:
        return pd.DataFrame(columns=["Date", "Ticker", *PRICE_COLUMNS])

    if isinstance(downloaded.columns, pd.MultiIndex):
        # yfinance no siempre entrega el MultiIndex en el mismo orden entre
        # versiones y combinaciones de tickers; este bloque lo normaliza.
        if not set(tickers).intersection(set(downloaded.columns.get_level_values(0))) and set(tickers).intersection(
            set(downloaded.columns.get_level_values(1))
        ):
            downloaded = downloaded.swaplevel(axis=1)
        frames: list[pd.DataFrame] = []
        for ticker in tickers:
            if ticker not in downloaded.columns.get_level_values(0):
                continue
            ticker_frame = downloaded[ticker].copy()
            ticker_frame = ticker_frame.reset_index()
            if "Date" not in ticker_frame.columns:
                ticker_frame = ticker_frame.rename(columns={ticker_frame.columns[0]: "Date"})
            ticker_frame.insert(1, "Ticker", ticker)
            frames.append(ticker_frame)
        if not frames:
            return pd.DataFrame(columns=["Date", "Ticker", *PRICE_COLUMNS])
        normalized = pd.concat(frames, ignore_index=True)
    else:
        # Para un solo ticker yfinance puede devolver columnas simples; en ese
        # caso reinyectamos el ticker explícitamente para mantener el contrato.
        ticker = tickers[0] if tickers else "UNKNOWN"
        normalized = downloaded.copy().reset_index()
        if "Date" not in normalized.columns:
            normalized = normalized.rename(columns={normalized.columns[0]: "Date"})
        normalized.insert(1, "Ticker", ticker)

    for column in PRICE_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    normalized["Date"] = pd.to_datetime(normalized["Date"], errors="coerce")
    # El orden por ticker y fecha simplifica luego tanto la validación operativa
    # como el consumo por el análisis y los scripts generados.
    normalized = normalized.dropna(subset=["Date", "Ticker"]).sort_values(["Ticker", "Date"]).reset_index(drop=True)
    return normalized


def persist_download_artifacts(
    request: FinancialDataRequest,
    downloaded: pd.DataFrame,
    normalized: pd.DataFrame,
) -> tuple[DataDownloadArtifacts, DataDownloadSummary]:
    """Guarda request, descarga cruda, descarga normalizada y metadatos de apoyo."""
    # Separamos bruto y normalizado para poder inspeccionar si un problema viene
    # de la fuente externa o de nuestra transformación posterior.
    RESULTS_DATA_REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DATA_NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    run_id = _timestamp()
    request_path = RESULTS_DATA_REQUESTS_DIR / f"request_{run_id}.json"
    raw_data_path = RESULTS_DATA_RAW_DIR / f"raw_{run_id}.csv"
    normalized_data_path = RESULTS_DATA_NORMALIZED_DIR / f"normalized_{run_id}.csv"
    metadata_path = RESULTS_DATA_RAW_DIR / f"raw_{run_id}.metadata.json"

    request_path.write_text(json.dumps(request.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    downloaded.to_csv(raw_data_path)
    normalized.to_csv(normalized_data_path, index=False)

    tickers_found = sorted({str(ticker).strip() for ticker in normalized["Ticker"].tolist() if str(ticker).strip()})
    metadata = {
        "provider": request.provider,
        "tickers_requested": request.tickers,
        "tickers_found": tickers_found,
        "interval": request.interval,
        "period": request.period,
        "start": request.start,
        "end": request.end,
        "download_timestamp": datetime.now().isoformat(timespec="seconds"),
        "raw_data_path": str(raw_data_path),
        "normalized_data_path": str(normalized_data_path),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # artifacts se usa para rutas completas; summary se usa como contexto breve
    # que puede viajar de nodo en nodo sin cargar ficheros.
    artifacts = DataDownloadArtifacts(
        request_path=str(request_path),
        raw_data_path=str(raw_data_path),
        normalized_data_path=str(normalized_data_path),
        metadata_path=str(metadata_path),
    )
    summary = DataDownloadSummary(
        provider=request.provider,
        tickers_requested=request.tickers,
        tickers_found=tickers_found,
        interval=request.interval,
        period=request.period,
        start=request.start,
        end=request.end,
        row_count=int(len(normalized)),
        columns=[str(column) for column in normalized.columns.tolist()],
    )
    return artifacts, summary
