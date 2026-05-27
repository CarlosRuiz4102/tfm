from __future__ import annotations

from pathlib import Path
from typing import Iterable

import math
import pandas as pd


PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def _normalize_ticker(value: object) -> str:
    return str(value).strip()


def _load_yfinance_wide_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=None)
    if raw.shape[0] < 4 or raw.shape[1] < 2:
        raise ValueError(f"CSV sin suficientes filas/columnas: {path}")

    first_cell = str(raw.iloc[0, 0]).strip().lower()
    second_cell = str(raw.iloc[1, 0]).strip().lower()
    if first_cell != "ticker" or second_cell != "price":
        raise ValueError("No es un CSV ancho de yfinance")

    tickers = [_normalize_ticker(value) for value in raw.iloc[0, 1:].tolist()]
    fields = [str(value).strip() for value in raw.iloc[1, 1:].tolist()]
    data = raw.iloc[3:].copy()
    data.columns = ["Date"] + [f"{ticker}|{field}" for ticker, field in zip(tickers, fields)]
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

    frames: list[pd.DataFrame] = []
    for ticker in sorted({ticker for ticker in tickers if ticker and ticker.lower() != "nan"}):
        columns = ["Date"]
        rename_map: dict[str, str] = {}
        for field in PRICE_COLUMNS:
            source = f"{ticker}|{field}"
            if source in data.columns:
                columns.append(source)
                rename_map[source] = field
        if len(columns) == 1:
            continue
        ticker_df = data[columns].rename(columns=rename_map).copy()
        ticker_df.insert(1, "Ticker", ticker)
        frames.append(ticker_df)

    if not frames:
        raise ValueError(f"No se pudieron extraer tickers del CSV: {path}")

    output = pd.concat(frames, ignore_index=True)
    for column in PRICE_COLUMNS:
        if column in output.columns:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    return output.dropna(subset=["Date", "Ticker", "Close"]).sort_values(["Ticker", "Date"]).reset_index(drop=True)


def _load_simple_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Date" not in df.columns:
        raise ValueError(f"El CSV no contiene columna Date: {path}")
    if "Ticker" not in df.columns:
        df.insert(1, "Ticker", path.stem.upper())
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in PRICE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(subset=["Date", "Ticker", "Close"]).sort_values(["Ticker", "Date"]).reset_index(drop=True)


def load_market_data(csv_paths: Iterable[str], tickers: Iterable[str] | None = None) -> pd.DataFrame:
    """Carga los CSV del proyecto y devuelve una tabla larga normalizada."""
    frames: list[pd.DataFrame] = []
    for raw_path in csv_paths:
        path = Path(raw_path)
        try:
            frames.append(_load_yfinance_wide_csv(path))
        except ValueError:
            frames.append(_load_simple_csv(path))

    if not frames:
        raise ValueError("No se recibieron CSV para cargar.")

    df = pd.concat(frames, ignore_index=True)
    requested = {_normalize_ticker(ticker) for ticker in (tickers or []) if _normalize_ticker(ticker)}
    if requested:
        df = df[df["Ticker"].isin(requested)].copy()
        if df.empty:
            raise ValueError(f"Ninguno de los tickers solicitados aparece en los CSV: {sorted(requested)}")

    return df.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def load_close_prices(csv_paths: Iterable[str], tickers: Iterable[str] | None = None) -> pd.DataFrame:
    """Devuelve cierres en formato ancho: indice Date y una columna por ticker."""
    df = load_market_data(csv_paths, tickers)
    close = df.pivot_table(index="Date", columns="Ticker", values="Close", aggfunc="last").sort_index()
    requested = [_normalize_ticker(ticker) for ticker in (tickers or []) if _normalize_ticker(ticker)]
    if requested:
        available = [ticker for ticker in requested if ticker in close.columns]
        if not available:
            raise ValueError(f"Ninguno de los tickers solicitados aparece en cierres: {requested}")
        close = close[available]
    return close.dropna(how="all")


def ticker_summary(df: pd.DataFrame) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for ticker, group in df.groupby("Ticker"):
        ordered = group.sort_values("Date")
        start_close = float(ordered["Close"].iloc[0])
        end_close = float(ordered["Close"].iloc[-1])
        pct_change = ((end_close / start_close) - 1.0) * 100 if start_close else None
        returns = ordered["Close"].pct_change().dropna()
        summaries.append(
            {
                "ticker": str(ticker),
                "rows": int(len(ordered)),
                "start_date": ordered["Date"].iloc[0].date().isoformat(),
                "end_date": ordered["Date"].iloc[-1].date().isoformat(),
                "start_close": round(start_close, 6),
                "end_close": round(end_close, 6),
                "absolute_change": round(end_close - start_close, 6),
                "percentage_change": round(pct_change, 6) if pct_change is not None else None,
                "mean_return_pct": round(float(returns.mean() * 100), 6) if len(returns) else None,
                "volatility_pct": round(float(returns.std() * 100), 6) if len(returns) > 1 else None,
                "min_close": round(float(ordered["Close"].min()), 6),
                "max_close": round(float(ordered["Close"].max()), 6),
            }
        )
    return summaries


def make_json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except (ValueError, TypeError):
            pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    return value
