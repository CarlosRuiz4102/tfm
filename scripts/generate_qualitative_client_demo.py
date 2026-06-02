from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_qualitative_demo_report import DEMO_CASES
from src.config import RESULTS_DIR
from src.execution.market_data import load_close_prices, load_market_data, make_json_safe


REPORT_PATH = RESULTS_DIR / "reports" / "salidas_demo_cliente_evaluacion_cualitativa.md"


def _pct(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/d"
    return f"{value * 100:.2f}%"


def _num(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/d"
    return f"{value:.2f}"


def _max_drawdown(close: pd.Series) -> float | None:
    close = close.dropna()
    if close.empty:
        return None
    running_max = close.cummax()
    drawdown = close / running_max - 1
    return float(drawdown.min())


def _series_points(series: pd.Series, max_points: int = 12) -> list[dict[str, Any]]:
    series = series.dropna()
    if series.empty:
        return []
    if len(series) > max_points:
        idx = [round(i * (len(series) - 1) / (max_points - 1)) for i in range(max_points)]
        series = series.iloc[sorted(set(idx))]
    return [{"date": str(index.date()), "value": round(float(value), 4)} for index, value in series.items()]


def _asset_metrics(close: pd.Series, annualization: float = 252.0) -> dict[str, Any]:
    close = close.dropna()
    returns = close.pct_change().dropna()
    if close.empty:
        return {}
    return make_json_safe(
        {
            "precio_inicial": float(close.iloc[0]),
            "precio_final": float(close.iloc[-1]),
            "rentabilidad_total": float(close.iloc[-1] / close.iloc[0] - 1),
            "maximo": float(close.max()),
            "minimo": float(close.min()),
            "volatilidad_anualizada": float(returns.std() * math.sqrt(annualization)) if len(returns) > 1 else None,
            "max_drawdown": _max_drawdown(close),
            "mejor_periodo": float(returns.max()) if not returns.empty else None,
            "peor_periodo": float(returns.min()) if not returns.empty else None,
            "fecha_inicio": str(close.index.min().date()),
            "fecha_fin": str(close.index.max().date()),
        }
    )


def _build_case_output(case: dict[str, Any]) -> dict[str, Any]:
    payload = case["input"]
    tickers = payload["tickers"]
    close = load_close_prices(payload["csv_paths"], tickers)
    annualization = 252.0 if payload.get("interval", "1d") == "1d" else 252.0 * 6.5

    metrics_by_ticker = {
        ticker: _asset_metrics(close[ticker], annualization=annualization)
        for ticker in close.columns
    }
    returns = close.pct_change().dropna()
    correlation = None
    if len(close.columns) > 1 and not returns.empty:
        correlation = returns.corr().round(4).to_dict()

    normalized = close.divide(close.iloc[0]).multiply(100)
    output: dict[str, Any] = {
        "analysis_type": payload.get("intent"),
        "level": case["level"],
        "metrics": metrics_by_ticker,
        "summary": "",
        "chart_data": {},
    }
    if correlation is not None:
        output["correlation"] = make_json_safe(correlation)

    query = payload["query"].lower()
    if case["level"] in {"B", "C"} or "grafica" in query or "normalizada" in query:
        if len(close.columns) > 1:
            output["chart_data"]["normalized_to_100"] = {
                ticker: _series_points(normalized[ticker])
                for ticker in normalized.columns
            }
        else:
            ticker = close.columns[0]
            output["chart_data"]["close_price"] = {ticker: _series_points(close[ticker])}

    if case["level"] == "C" or "drawdown" in query or "riesgo" in query:
        output["chart_data"]["drawdown"] = {}
        for ticker in close.columns:
            series = close[ticker].dropna()
            drawdown = series / series.cummax() - 1
            output["chart_data"]["drawdown"][ticker] = _series_points(drawdown)

    if "media" in query or "tecnico" in query:
        ticker = close.columns[0]
        output["technical"] = {
            "sma_20": float(close[ticker].rolling(20).mean().dropna().iloc[-1]) if len(close[ticker].dropna()) >= 20 else None,
            "sma_50": float(close[ticker].rolling(50).mean().dropna().iloc[-1]) if len(close[ticker].dropna()) >= 50 else None,
            "ultimo_cierre": float(close[ticker].dropna().iloc[-1]),
        }

    if "volumen" in query or case["level"] == "C":
        data = load_market_data(payload["csv_paths"], tickers)
        if "Volume" in data.columns:
            volume = data.groupby("Ticker")["Volume"].mean(numeric_only=True).to_dict()
            output["volume"] = make_json_safe({ticker: float(value) for ticker, value in volume.items()})

    output["summary"] = _summary_for_client(case, output)
    return make_json_safe(output)


def _summary_for_client(case: dict[str, Any], output: dict[str, Any]) -> str:
    metrics = output["metrics"]
    level = case["level"]
    tickers = list(metrics)
    if not tickers:
        return "No hay datos suficientes para generar el analisis."

    if len(tickers) == 1:
        ticker = tickers[0]
        item = metrics[ticker]
        text = (
            f"Para {ticker}, entre {item['fecha_inicio']} y {item['fecha_fin']}, "
            f"el precio paso de {_num(item['precio_inicial'])} a {_num(item['precio_final'])}, "
            f"con una rentabilidad total de {_pct(item['rentabilidad_total'])}. "
            f"El maximo drawdown fue {_pct(item['max_drawdown'])} y la volatilidad anualizada aproximada fue "
            f"{_pct(item['volatilidad_anualizada'])}."
        )
        if "technical" in output:
            tech = output["technical"]
            text += (
                f" El ultimo cierre fue {_num(tech['ultimo_cierre'])}, frente a una SMA20 de "
                f"{_num(tech['sma_20'])} y una SMA50 de {_num(tech['sma_50'])}."
            )
    else:
        ranked = sorted(tickers, key=lambda t: metrics[t]["rentabilidad_total"], reverse=True)
        parts = [
            f"{ticker}: rentabilidad {_pct(metrics[ticker]['rentabilidad_total'])}, "
            f"volatilidad {_pct(metrics[ticker]['volatilidad_anualizada'])}, "
            f"drawdown {_pct(metrics[ticker]['max_drawdown'])}"
            for ticker in ranked
        ]
        text = (
            f"La comparativa ordena mejor a {ranked[0]} por rentabilidad historica en el periodo. "
            + " | ".join(parts)
            + "."
        )
        if output.get("correlation"):
            text += " La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida."

    if level == "A":
        text += " Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado."
    elif level == "B":
        text += " Lectura: se acompana de datos para una grafica principal porque el usuario pide un analisis mas completo."
    else:
        text += " Lectura: se incluyen metricas y datos visuales adicionales porque el usuario pide un analisis profesional o multicriterio."

    return text + " El analisis es historico y descriptivo; no constituye recomendacion de inversion."


def _metric_table(output: dict[str, Any]) -> list[str]:
    lines = [
        "| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for ticker, item in output["metrics"].items():
        lines.append(
            f"| {ticker} | {_num(item['precio_inicial'])} | {_num(item['precio_final'])} | "
            f"{_pct(item['rentabilidad_total'])} | {_pct(item['volatilidad_anualizada'])} | "
            f"{_pct(item['max_drawdown'])} | {_num(item['maximo'])} | {_num(item['minimo'])} |"
        )
    return lines


def _json_block(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > 4500:
        return text[:4500] + "\n... [salida truncada en el informe]"
    return text


def main() -> int:
    results = [(case, _build_case_output(case)) for case in DEMO_CASES]
    lines = [
        "# Demo ejecutada de salidas cliente A/B/C",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Este documento muestra una ejecución local reproducible sobre los CSV reales del proyecto.",
        "Se usa para visualizar como quedarian las salidas que recibira el cliente en los niveles A, B y C.",
        "",
        "> Nota: la ejecucion LLM real con el endpoint universitario se intento, pero no completo dentro del tiempo disponible. Por eso este documento no compara modelos; muestra la salida calculada desde datos reales y redactada con una plantilla local para validar la presentacion.",
        "",
        "## Resumen de casos",
        "",
        "| ID | Nivel | Salida esperada |",
        "|---|---:|---|",
    ]
    for case, _ in results:
        lines.append(f"| `{case['id']}` | {case['level']} | {case['expected_depth']} |")

    for case, output in results:
        lines.extend(
            [
                "",
                f"## {case['id']} - Nivel {case['level']}",
                "",
                f"**Consulta:** {case['input']['query']}",
                "",
                "### Lo que mostrariamos al cliente",
                "",
                * _metric_table(output),
                "",
                output["summary"],
                "",
                "### Datos para visualizacion o trazabilidad",
                "",
                "```json",
                _json_block({key: value for key, value in output.items() if key not in {"summary"}}),
                "```",
            ]
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Informe escrito en: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
