from __future__ import annotations

from pathlib import Path

from src.config import RAW_DATA_DIR


def _raw(path_name: str) -> str:
    return str((RAW_DATA_DIR / path_name).resolve())


SAMPLE_INPUTS = {
    "growth_nvda": {
        "query": "Cuanto ha crecido Nvidia en 5 anos",
        "intent": "price_growth",
        "tickers": ["NVDA"],
        "start": None,
        "end": None,
        "period": "5y",
        "interval": "1d",
        "csv_paths": [_raw("cunto_ha_crecido_nvidia_en_5_aos.csv")],
        "warnings": [],
    },
    "compare_nvda_amd": {
        "query": "Compara Nvidia y AMD en 2 anos",
        "intent": "compare_assets",
        "tickers": ["NVDA", "AMD"],
        "start": None,
        "end": None,
        "period": "2y",
        "interval": "1d",
        "csv_paths": [_raw("compara_nvidia_y_amd_en_2_aos.csv")],
        "warnings": [],
    },
    "overview_aapl": {
        "query": "Dame una vision general de AAPL en 3 meses",
        "intent": "asset_overview",
        "tickers": ["AAPL"],
        "start": None,
        "end": None,
        "period": "3mo",
        "interval": "1d",
        "csv_paths": [_raw("aapl_en_3_meses.csv")],
        "warnings": [],
    },
    "returns_qqq_spy": {
        "query": "Analiza los retornos de QQQ y SPY en 2024",
        "intent": "return_analysis",
        "tickers": ["QQQ", "SPY"],
        "start": "2024-01-01",
        "end": "2024-12-31",
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
        "warnings": [],
    },
}
