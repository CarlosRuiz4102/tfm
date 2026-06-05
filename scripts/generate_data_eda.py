from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CATALOG_PATH = ROOT / "data" / "catalog" / "query_cases.json"
PROCESSED_DIR = ROOT / "data" / "processed"
DOCS_DIR = ROOT / "docs"
NOTEBOOKS_DIR = ROOT / "notebooks"

LONG_DATA_PATH = PROCESSED_DIR / "eda_dataset_largo.csv"
CASE_SUMMARY_PATH = PROCESSED_DIR / "eda_resumen_ficheros.csv"
SERIES_SUMMARY_PATH = PROCESSED_DIR / "eda_resumen_series.csv"
REPORT_PATH = DOCS_DIR / "eda_datos_tfm.txt"
NOTEBOOK_PATH = NOTEBOOKS_DIR / "03_eda_datos_tfm.ipynb"

FIELD_ORDER = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def read_yfinance_csv(path: Path) -> pd.DataFrame:
    """Read a yfinance CSV saved with MultiIndex columns."""
    df = pd.read_csv(path, header=[0, 1], index_col=0)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df.sort_index()
    return df


def metadata_for(csv_path: Path) -> dict:
    meta_path = csv_path.with_suffix(".metadata.json")
    if not meta_path.exists():
        return {}
    return load_json(meta_path)


def case_id_from_path(path: Path) -> str:
    return path.stem


def query_label_from_meta(meta: dict) -> str | None:
    return meta.get("analysis_label") or meta.get("query_label")


def to_long(case_id: str, csv_path: Path, meta: dict, wide: pd.DataFrame) -> pd.DataFrame:
    records = []
    tickers = sorted({str(ticker) for ticker, _ in wide.columns})
    for ticker in tickers:
        sub = wide[ticker].copy()
        for field in FIELD_ORDER:
            if field not in sub.columns:
                sub[field] = np.nan
        sub = sub[FIELD_ORDER]
        sub = sub.reset_index(names="datetime")
        sub.insert(0, "ticker", ticker)
        sub.insert(0, "interval", meta.get("interval"))
        sub.insert(0, "period", meta.get("period"))
        sub.insert(0, "end", meta.get("end"))
        sub.insert(0, "start", meta.get("start"))
        sub.insert(0, "query_label", query_label_from_meta(meta))
        sub.insert(0, "query", meta.get("query"))
        sub.insert(0, "source_file", csv_path.name)
        sub.insert(0, "case_id", case_id)
        records.append(sub)
    if not records:
        return pd.DataFrame()
    return pd.concat(records, ignore_index=True)


def annualization_factor(interval: str | None) -> int:
    if interval in {"1h", "60m", "90m"}:
        return 24 * 252
    if interval in {"1m", "2m", "5m", "15m", "30m"}:
        return 252
    return 252


def max_drawdown(close: pd.Series) -> float:
    close = close.dropna()
    if close.empty:
        return np.nan
    running_max = close.cummax()
    drawdown = close / running_max - 1
    return float(drawdown.min())


def summarize_case(case_id: str, csv_path: Path, meta: dict, wide: pd.DataFrame) -> dict:
    tickers = sorted({str(ticker) for ticker, _ in wide.columns})
    close_cols = [(ticker, "Close") for ticker in tickers if (ticker, "Close") in wide.columns]
    close = wide.loc[:, close_cols] if close_cols else pd.DataFrame(index=wide.index)
    total_cells = int(wide.size)
    missing_cells = int(wide.isna().sum().sum())
    duplicated_dates = int(wide.index.duplicated().sum())
    return {
        "case_id": case_id,
        "source_file": csv_path.name,
        "query": meta.get("query"),
        "query_label": query_label_from_meta(meta),
        "tickers": ", ".join(tickers),
        "interval": meta.get("interval"),
        "start_param": meta.get("start"),
        "end_param": meta.get("end"),
        "period_param": meta.get("period"),
        "rows": int(len(wide)),
        "columns": int(len(wide.columns)),
        "start_observed": wide.index.min().date().isoformat() if len(wide.index) else "",
        "end_observed": wide.index.max().date().isoformat() if len(wide.index) else "",
        "missing_cells": missing_cells,
        "missing_pct": round(missing_cells / total_cells * 100, 4) if total_cells else 0,
        "duplicated_dates": duplicated_dates,
        "close_columns": int(len(close.columns)),
    }


def summarize_series(long_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (case_id, source_file, query, query_label, interval, ticker), group in long_df.groupby(
        ["case_id", "source_file", "query", "query_label", "interval", "ticker"],
        dropna=False,
    ):
        group = group.sort_values("datetime")
        close = pd.to_numeric(group["Close"], errors="coerce").dropna()
        volume = pd.to_numeric(group["Volume"], errors="coerce")
        simple_returns = close.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        log_returns = np.log(close).diff().replace([np.inf, -np.inf], np.nan).dropna()
        ann_factor = annualization_factor(interval)
        rows.append(
            {
                "case_id": case_id,
                "source_file": source_file,
                "query": query,
                "query_label": query_label,
                "interval": interval,
                "ticker": ticker,
                "observations": int(len(group)),
                "start_observed": group["datetime"].min().date().isoformat(),
                "end_observed": group["datetime"].max().date().isoformat(),
                "missing_close": int(group["Close"].isna().sum()),
                "missing_volume": int(volume.isna().sum()),
                "zero_volume_rows": int((volume.fillna(0) == 0).sum()),
                "first_close": round(float(close.iloc[0]), 6) if len(close) else np.nan,
                "last_close": round(float(close.iloc[-1]), 6) if len(close) else np.nan,
                "total_return_pct": round((float(close.iloc[-1] / close.iloc[0] - 1) * 100), 4)
                if len(close) > 1 and close.iloc[0] != 0
                else np.nan,
                "mean_return_pct": round(float(simple_returns.mean() * 100), 4)
                if len(simple_returns)
                else np.nan,
                "volatility_ann_pct": round(float(log_returns.std() * np.sqrt(ann_factor) * 100), 4)
                if len(log_returns) > 1
                else np.nan,
                "min_daily_return_pct": round(float(simple_returns.min() * 100), 4)
                if len(simple_returns)
                else np.nan,
                "max_daily_return_pct": round(float(simple_returns.max() * 100), 4)
                if len(simple_returns)
                else np.nan,
                "max_drawdown_pct": round(max_drawdown(close) * 100, 4) if len(close) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def format_table(df: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    table = df.loc[:, columns].copy()
    if max_rows is not None:
        table = table.head(max_rows)
    return table.to_string(index=False)


def build_report(
    catalog: list[dict],
    case_summary: pd.DataFrame,
    series_summary: pd.DataFrame,
    long_df: pd.DataFrame,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tickers = sorted(long_df["ticker"].dropna().unique().tolist())
    query_labels = case_summary["query_label"].value_counts(dropna=False).rename_axis("query_label").reset_index(name="cases")
    intervals = case_summary["interval"].value_counts(dropna=False).rename_axis("interval").reset_index(name="cases")
    date_start = pd.to_datetime(long_df["datetime"], utc=True).min()
    date_end = pd.to_datetime(long_df["datetime"], utc=True).max()
    total_rows = len(long_df)
    total_cases = len(case_summary)
    total_series = len(series_summary)
    total_missing_close = int(series_summary["missing_close"].sum())
    zero_volume = int(series_summary["zero_volume_rows"].sum())
    catalog_tickers = sorted({ticker for case in catalog for ticker in case.get("tickers", [])})

    best_returns = series_summary.sort_values("total_return_pct", ascending=False)
    worst_drawdowns = series_summary.sort_values("max_drawdown_pct")
    quality = case_summary.sort_values(["missing_pct", "duplicated_dates"], ascending=False)

    lines = [
        "EDA DE DATOS DEL TFM",
        "=" * 70,
        f"Generado: {generated_at}",
        "",
        "1. Objetivo",
        "-" * 70,
        "Este documento resume el analisis exploratorio de los datos financieros",
        "usados en el MVP del TFM. El foco esta en comprobar cobertura temporal,",
        "calidad del dato, variedad de activos, estructura de los CSV y metricas",
        "basicas de precio, retorno, volatilidad y drawdown.",
        "",
        "2. Fuentes y trazabilidad",
        "-" * 70,
        "Fuente primaria: CSV descargados previamente con yfinance y versionados",
        "en data/raw. Cada CSV dispone de un fichero .metadata.json con query,",
        "etiqueta de consulta, tickers, intervalo y parametros de descarga.",
        "",
        f"Catalogo de queries: {CATALOG_PATH.relative_to(ROOT)}",
        f"Casos definidos en catalogo: {len(catalog)}",
        f"Tickers definidos en catalogo: {', '.join(catalog_tickers)}",
        f"CSV analizados: {total_cases}",
        f"Series ticker-caso analizadas: {total_series}",
        f"Filas normalizadas en formato largo: {total_rows}",
        f"Rango temporal observado: {date_start} -> {date_end}",
        "",
        "3. Estructura tecnica de los CSV",
        "-" * 70,
        "Los ficheros procedentes de yfinance se guardan con columnas multinivel:",
        "primer nivel = ticker y segundo nivel = campo OHLCV. Por eso no deben",
        "leerse como CSV planos con una sola fila de cabecera. El EDA los carga",
        "con header=[0, 1] e index_col=0 y despues los normaliza a formato largo.",
        "",
        "Campos esperados por ticker: Open, High, Low, Close, Adj Close, Volume.",
        "",
        "4. Cobertura por fichero",
        "-" * 70,
        format_table(
            case_summary,
            [
                "source_file",
                "query_label",
                "tickers",
                "interval",
                "rows",
                "start_observed",
                "end_observed",
                "missing_pct",
                "duplicated_dates",
            ],
        ),
        "",
        "5. Distribucion de etiquetas e intervalos",
        "-" * 70,
        "Etiquetas:",
        format_table(query_labels, ["query_label", "cases"]),
        "",
        "Intervalos:",
        format_table(intervals, ["interval", "cases"]),
        "",
        "6. Calidad del dato",
        "-" * 70,
        f"Nulos en Close: {total_missing_close}",
        f"Filas con volumen igual a cero o ausente: {zero_volume}",
        "Duplicados por fecha: ver columna duplicated_dates en la tabla de cobertura.",
        "",
        "Casos con mayor porcentaje de celdas ausentes:",
        format_table(
            quality,
            ["source_file", "tickers", "interval", "missing_pct", "duplicated_dates"],
            max_rows=10,
        ),
        "",
        "Lectura metodologica:",
        "- La ausencia de nulos en Close es clave porque las metricas del MVP",
        "  dependen de precios de cierre.",
        "- En divisas y futuros intradia puede aparecer volumen cero o no informado;",
        "  por tanto el volumen no debe tratarse como variable obligatoria para",
        "  todos los tipos de activo.",
        "- La mezcla de intervalos 1d y 1h es intencionada para probar consultas",
        "  historicas diarias e intradia, pero las metricas de volatilidad deben",
        "  interpretarse con su frecuencia correspondiente.",
        "",
        "7. Resumen por serie",
        "-" * 70,
        format_table(
            series_summary.sort_values(["source_file", "ticker"]),
            [
                "source_file",
                "ticker",
                "observations",
                "start_observed",
                "end_observed",
                "total_return_pct",
                "volatility_ann_pct",
                "max_drawdown_pct",
            ],
        ),
        "",
        "Mayores rentabilidades totales observadas:",
        format_table(
            best_returns,
            ["source_file", "ticker", "total_return_pct", "volatility_ann_pct", "max_drawdown_pct"],
            max_rows=5,
        ),
        "",
        "Mayores drawdowns observados:",
        format_table(
            worst_drawdowns,
            ["source_file", "ticker", "total_return_pct", "volatility_ann_pct", "max_drawdown_pct"],
            max_rows=5,
        ),
        "",
        "8. Valor para el TFM",
        "-" * 70,
        "El conjunto de datos cubre acciones individuales, ETFs, indice amplio,",
        "criptoactivo, divisa y futuro de materia prima. Esto permite probar si el",
        "sistema entiende consultas con distintos tipos de activo, horizontes",
        "temporales y objetivos analiticos.",
        "",
        "Para la memoria, este EDA justifica:",
        "- la seleccion de casos de prueba variados;",
        "- la necesidad de una capa de normalizacion de datos;",
        "- la separacion entre catalogo de queries, datos raw y datos procesados;",
        "- el uso de metricas financieras basicas como retorno, volatilidad y",
        "  drawdown para validar las respuestas del agente.",
        "",
        "9. Limitaciones detectadas",
        "-" * 70,
        "- Las descargas relativas por periodo, por ejemplo 3mo o 5y, dependen de la",
        "  fecha en que se genero el CSV. Para reproducibilidad completa se recomienda",
        "  fijar fecha de descarga o rango start/end en futuros datasets definitivos.",
        "- Los datos proceden de Yahoo Finance via yfinance; para un entorno productivo",
        "  habria que considerar disponibilidad, licencias y estabilidad del proveedor.",
        "",
        "10. Notebooks auxiliares conservados",
        "-" * 70,
        "Los notebooks 01_yfinance_eda_avanzado.ipynb y",
        "02_catalogo_queries_y_csv.ipynb se han reducido para eliminar analisis",
        "duplicados que ya cubre 03_eda_datos_tfm.ipynb. Permanecen solo por las",
        "funciones que no pertenecen al EDA formal:",
        "",
        "- 01_yfinance_eda_avanzado.ipynb queda como laboratorio complementario.",
        "  Permite probar en vivo nuevos tickers, periodos e intervalos con",
        "  yfinance antes de incorporarlos al catalogo. Es util para decidir si",
        "  un activo devuelve suficientes observaciones y si merece formar parte",
        "  del dataset congelado.",
        "",
        "- 02_catalogo_queries_y_csv.ipynb queda como pieza de trazabilidad del",
        "  dataset raw. Lee data/catalog/query_cases.json, valida cada caso,",
        "  genera el manifiesto de CSV esperados y permite regenerar data/raw",
        "  con sus metadatos cuando se active la descarga real.",
        "",
        "Para la memoria y el analisis formal, el notebook recomendado pasa a ser",
        "03_eda_datos_tfm.ipynb, apoyado por este informe TXT y por las tablas",
        "procesadas de data/processed. En otras palabras: 01 sirve para explorar",
        "posibles datos nuevos, 02 sirve para construir o regenerar el dataset,",
        "y 03 sirve para justificar y analizar el dataset definitivo.",
        "",
        "11. Artefactos generados",
        "-" * 70,
        f"- Dataset largo: {LONG_DATA_PATH.relative_to(ROOT)}",
        f"- Resumen por fichero: {CASE_SUMMARY_PATH.relative_to(ROOT)}",
        f"- Resumen por serie: {SERIES_SUMMARY_PATH.relative_to(ROOT)}",
        f"- Notebook reproducible: {NOTEBOOK_PATH.relative_to(ROOT)}",
        "",
    ]
    return "\n".join(lines)


def notebook_cell(cell_type: str, source: str) -> dict:
    base = {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.splitlines()],
    }
    if cell_type == "code":
        base["execution_count"] = None
        base["outputs"] = []
    return base


def build_notebook() -> dict:
    cells = [
        notebook_cell(
            "markdown",
            """# EDA de datos del TFM

Este notebook sustituye al EDA exploratorio interactivo para la parte formal del TFM. Trabaja solo con los CSV versionados en `data/raw`, por lo que no depende de descargar datos en vivo.
""",
        ),
        notebook_cell(
            "markdown",
            """## 1. Objetivo

Comprobar la calidad, cobertura y utilidad de los datos financieros usados por el MVP: estructura de los CSV, nulos, duplicados, rango temporal, variedad de activos, retornos, volatilidad y drawdown.
""",
        ),
        notebook_cell(
            "code",
            """from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

case_summary = pd.read_csv(PROCESSED_DIR / "eda_resumen_ficheros.csv")
series_summary = pd.read_csv(PROCESSED_DIR / "eda_resumen_series.csv")
long_df = pd.read_csv(PROCESSED_DIR / "eda_dataset_largo.csv", parse_dates=["datetime"])

case_summary""",
        ),
        notebook_cell(
            "markdown",
            """## 2. Normalización aplicada

Los CSV de `yfinance` tienen columnas multinivel: ticker y campo OHLCV. El generador `scripts/generate_data_eda.py` los lee con `header=[0, 1]`, conserva los metadatos y genera un dataset largo en `data/processed/eda_dataset_largo.csv`.
""",
        ),
        notebook_cell(
            "code",
            """long_df.head()""",
        ),
        notebook_cell(
            "markdown",
            """## 3. Cobertura y calidad

La tabla siguiente resume filas, rango observado, porcentaje de nulos y duplicados por fecha para cada CSV.
""",
        ),
        notebook_cell(
            "code",
            """case_summary[[
    "source_file", "query_label", "tickers", "interval", "rows",
    "start_observed", "end_observed", "missing_pct", "duplicated_dates"
]]""",
        ),
        notebook_cell(
            "code",
            """fig, ax = plt.subplots(figsize=(9, 4))
case_summary.sort_values("rows").plot.barh(x="source_file", y="rows", ax=ax, legend=False)
ax.set_title("Observaciones por fichero")
ax.set_xlabel("Filas")
ax.set_ylabel("")
plt.tight_layout()""",
        ),
        notebook_cell(
            "markdown",
            """## 4. Resumen financiero por serie

Se calculan rentabilidad total, volatilidad anualizada aproximada y drawdown máximo por cada combinación fichero-ticker.
""",
        ),
        notebook_cell(
            "code",
            """series_summary[[
    "source_file", "ticker", "observations", "start_observed", "end_observed",
    "total_return_pct", "volatility_ann_pct", "max_drawdown_pct"
]].sort_values(["source_file", "ticker"])""",
        ),
        notebook_cell(
            "code",
            """fig, ax = plt.subplots(figsize=(9, 4))
plot_df = series_summary.sort_values("total_return_pct")
ax.barh(plot_df["ticker"] + " | " + plot_df["source_file"].str.slice(0, 24), plot_df["total_return_pct"])
ax.set_title("Rentabilidad total por serie")
ax.set_xlabel("Rentabilidad total (%)")
plt.tight_layout()""",
        ),
        notebook_cell(
            "code",
            """fig, ax = plt.subplots(figsize=(9, 4))
plot_df = series_summary.sort_values("max_drawdown_pct")
ax.barh(plot_df["ticker"] + " | " + plot_df["source_file"].str.slice(0, 24), plot_df["max_drawdown_pct"])
ax.set_title("Drawdown maximo por serie")
ax.set_xlabel("Drawdown maximo (%)")
plt.tight_layout()""",
        ),
        notebook_cell(
            "markdown",
            """## 5. Ejemplos de series de cierre

Este bloque permite inspeccionar visualmente varias series normalizadas a base 100. Se agrupa por caso para evitar mezclar horizontes temporales incompatibles.
""",
        ),
        notebook_cell(
            "code",
            """for case_id, group in long_df.groupby("case_id"):
    pivot = group.pivot(index="datetime", columns="ticker", values="Close").dropna(how="all")
    if pivot.empty:
        continue
    norm = pivot / pivot.iloc[0] * 100
    ax = norm.plot(figsize=(9, 4), title=f"Evolucion normalizada base 100 - {case_id}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Base 100")
    plt.tight_layout()
    plt.show()""",
        ),
        notebook_cell(
            "markdown",
            """## 6. Conclusiones para la memoria

- El dataset cubre acciones, ETFs, indice amplio, criptoactivo, divisa y futuro de materia prima.
- La capa de normalizacion es necesaria porque la salida de `yfinance` no es plana.
- La calidad de `Close` es suficiente para las metricas principales del MVP.
- El volumen debe usarse con prudencia en divisas e instrumentos intradia.
- Para versiones finales conviene fijar rangos absolutos cuando sea posible, ya que los periodos relativos dependen de la fecha de descarga.
""",
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

    catalog = load_json(CATALOG_PATH)
    long_parts = []
    case_rows = []
    for csv_path in sorted(RAW_DIR.glob("*.csv")):
        meta = metadata_for(csv_path)
        case_id = case_id_from_path(csv_path)
        wide = read_yfinance_csv(csv_path)
        long_parts.append(to_long(case_id, csv_path, meta, wide))
        case_rows.append(summarize_case(case_id, csv_path, meta, wide))

    long_df = pd.concat(long_parts, ignore_index=True)
    case_summary = pd.DataFrame(case_rows)
    series_summary = summarize_series(long_df)

    long_df.to_csv(LONG_DATA_PATH, index=False, encoding="utf-8")
    case_summary.to_csv(CASE_SUMMARY_PATH, index=False, encoding="utf-8")
    series_summary.to_csv(SERIES_SUMMARY_PATH, index=False, encoding="utf-8")
    REPORT_PATH.write_text(build_report(catalog, case_summary, series_summary, long_df), encoding="utf-8")
    NOTEBOOK_PATH.write_text(json.dumps(build_notebook(), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated {LONG_DATA_PATH.relative_to(ROOT)}")
    print(f"Generated {CASE_SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Generated {SERIES_SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Generated {REPORT_PATH.relative_to(ROOT)}")
    print(f"Generated {NOTEBOOK_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
