from __future__ import annotations

from pathlib import Path

import pandas as pd


def csv_exists(csv_path: str) -> bool:
    return Path(csv_path).exists()


def load_market_data(csv_paths: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for csv_path in csv_paths:
        raw = pd.read_csv(csv_path, header=[0, 1])
        if str(raw.iloc[0, 0]).strip().lower() == "date":
            raw = raw.iloc[1:].reset_index(drop=True)
        raw.columns = pd.MultiIndex.from_tuples([("meta", "Date")] + list(raw.columns[1:]))
        raw[("meta", "Date")] = pd.to_datetime(raw[("meta", "Date")], errors="coerce")
        raw = raw.dropna(subset=[("meta", "Date")])

        ticker_names: list[str] = []
        for top_level, _ in raw.columns[1:]:
            if top_level != "meta" and top_level not in ticker_names:
                ticker_names.append(top_level)

        for ticker in ticker_names:
            subset = raw.loc[:, [("meta", "Date")] + [col for col in raw.columns[1:] if col[0] == ticker]].copy()
            subset.columns = ["Date"] + [col[1] for col in subset.columns[1:]]
            subset["Ticker"] = ticker
            frames.append(subset)

    if not frames:
        raise ValueError("No se pudo construir un DataFrame a partir de los CSV.")

    market = pd.concat(frames, ignore_index=True)
    market["Close"] = pd.to_numeric(market["Close"], errors="coerce")
    market = market.dropna(subset=["Date", "Ticker", "Close"])
    return market.sort_values(["Ticker", "Date"]).reset_index(drop=True)
