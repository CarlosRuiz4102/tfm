from __future__ import annotations

from pathlib import Path

from src.config import RAW_DATA_DIR


def _raw(path_name: str) -> str:
    return str((RAW_DATA_DIR / path_name).resolve())


SAMPLE_INPUTS = {
    "growth_nvda": {
        "query": "Cuanto ha crecido Nvidia en 5 anos",
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
        "tickers": ["QQQ", "SPY"],
        "start": "2024-01-01",
        "end": "2024-12-31",
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
        "warnings": [],
    },
    "risk_qqq_spy": {
        "query": "Analiza el riesgo historico de QQQ y SPY en 2024",
        "tickers": ["QQQ", "SPY"],
        "start": "2024-01-01",
        "end": "2024-12-31",
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
        "warnings": [],
    },
    "technical_aapl": {
        "query": "Haz un analisis tecnico de AAPL en 3 meses",
        "tickers": ["AAPL"],
        "start": None,
        "end": None,
        "period": "3mo",
        "interval": "1d",
        "csv_paths": [_raw("aapl_en_3_meses.csv")],
        "warnings": [],
    },
    "complex_nvda_growth_report": {
        "query": (
            "Analiza Nvidia en los ultimos 5 anos: calcula precio inicial y final, "
            "crecimiento absoluto, crecimiento porcentual, maximo, minimo, volatilidad "
            "diaria y una conclusion breve sin recomendar inversion."
        ),
        "tickers": ["NVDA"],
        "start": None,
        "end": None,
        "period": "5y",
        "interval": "1d",
        "csv_paths": [_raw("cunto_ha_crecido_nvidia_en_5_aos.csv")],
        "warnings": [],
    },
    "complex_nvda_amd_ranking": {
        "query": (
            "Compara NVDA y AMD en 2 anos con una tabla: rentabilidad total, "
            "volatilidad diaria, mejor y peor cierre, drawdown aproximado y ranking final "
            "por comportamiento historico."
        ),
        "tickers": ["NVDA", "AMD"],
        "start": None,
        "end": None,
        "period": "2y",
        "interval": "1d",
        "csv_paths": [_raw("compara_nvidia_y_amd_en_2_aos.csv")],
        "warnings": [],
    },
    "complex_aapl_overview_volume": {
        "query": (
            "Dame una vision general de AAPL en 3 meses incluyendo tendencia del cierre, "
            "rango de precios, dias de mayor volumen y si el activo termino por encima "
            "o por debajo del inicio."
        ),
        "tickers": ["AAPL"],
        "start": None,
        "end": None,
        "period": "3mo",
        "interval": "1d",
        "csv_paths": [_raw("aapl_en_3_meses.csv")],
        "warnings": [],
    },
    "complex_aapl_technical_context": {
        "query": (
            "Haz un analisis tecnico de AAPL en 3 meses con medias moviles simples "
            "de 20 y 50 sesiones, volatilidad reciente, ultimo cierre frente a las medias "
            "y una interpretacion prudente."
        ),
        "tickers": ["AAPL"],
        "start": None,
        "end": None,
        "period": "3mo",
        "interval": "1d",
        "csv_paths": [_raw("aapl_en_3_meses.csv")],
        "warnings": [],
    },
    "complex_qqq_spy_risk_return": {
        "query": (
            "Compara QQQ y SPY durante 2024 calculando rentabilidad acumulada, "
            "rentabilidad media diaria, volatilidad diaria, correlacion entre ambos "
            "y una conclusion sobre cual fue mas rentable y cual fue mas volatil."
        ),
        "tickers": ["QQQ", "SPY"],
        "start": "2024-01-01",
        "end": "2024-12-31",
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
        "warnings": [],
    },
    "complex_qqq_spy_drawdown": {
        "query": (
            "Analiza el riesgo de QQQ y SPY en 2024: calcula volatilidad, maximo drawdown, "
            "peor dia, mejor dia y explica las diferencias de riesgo sin hacer recomendaciones."
        ),
        "tickers": ["QQQ", "SPY"],
        "start": "2024-01-01",
        "end": "2024-12-31",
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("qqq_y_spy_desde_20240101_hasta_20241231.csv")],
        "warnings": [],
    },
    "complex_btc_2024_profile": {
        "query": (
            "Analiza Bitcoin en 2024 con rentabilidad acumulada, volatilidad, maximo, "
            "minimo, mejor dia, peor dia y un resumen claro de su comportamiento historico."
        ),
        "tickers": ["BTC-USD"],
        "start": "2024-01-01",
        "end": "2024-12-31",
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("datos_de_bitcoin_desde_20240101_hasta_20241231.csv")],
        "warnings": [],
    },
    "complex_sp500_since_2020": {
        "query": (
            "Resume el S&P 500 desde 2020: calcula crecimiento total, maximo, minimo, "
            "volatilidad historica, drawdown aproximado y divide la respuesta en metricas "
            "y conclusion."
        ),
        "tickers": ["^GSPC"],
        "start": "2020-01-01",
        "end": None,
        "period": None,
        "interval": "1d",
        "csv_paths": [_raw("descrgame_el_histrico_del_sp_500_desde_2020.csv")],
        "warnings": [],
    },
    "complex_eurusd_intraday": {
        "query": (
            "Analiza EUR/USD en 10 dias a 1h: calcula rango intradia aproximado, "
            "cambio porcentual, volatilidad por hora y describe si el movimiento fue "
            "estable o irregular."
        ),
        "tickers": ["EURUSD=X"],
        "start": None,
        "end": None,
        "period": "10d",
        "interval": "1h",
        "csv_paths": [_raw("eurusd_en_10_das_a_1h.csv")],
        "warnings": [],
    },
    "complex_gold_intraday": {
        "query": (
            "Analiza el oro en 1 semana a 1h calculando cambio total, rango maximo-minimo, "
            "volatilidad horaria, sesiones con mayor volumen y una conclusion historica breve."
        ),
        "tickers": ["GC=F"],
        "start": None,
        "end": None,
        "period": "1wk",
        "interval": "1h",
        "csv_paths": [_raw("quiero_el_oro_en_1_semana_a_1h.csv")],
        "warnings": [],
    },
}
