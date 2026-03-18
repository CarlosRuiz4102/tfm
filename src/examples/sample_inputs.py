from __future__ import annotations

from pathlib import Path

from src.config import RAW_DATA_DIR


def _raw(path_name: str) -> str:
    return str((RAW_DATA_DIR / path_name).resolve())


SAMPLE_INPUTS = {
    "growth_nvda": {
        "query": "Cuánto ha crecido Nvidia en 5 años",
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
        "query": "Compara Nvidia y AMD en 2 años",
        "intent": "compare_assets",
        "tickers": ["NVDA", "AMD"],
        "start": None,
        "end": None,
        "period": "2y",
        "interval": "1d",
        "csv_paths": [_raw("compara_nvidia_y_amd_en_2_aos.csv")],
        "warnings": [],
    },
}
