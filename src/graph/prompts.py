from __future__ import annotations

from textwrap import dedent

from src.agents import build_analysis_plan as build_agent_analysis_plan
from src.agents import build_code_body
from src.schemas import AnalysisPlan, FinancialQueryInput


def build_analysis_plan(query_input: FinancialQueryInput) -> AnalysisPlan:
    return build_agent_analysis_plan(query_input)


def build_code_template(plan: AnalysisPlan) -> str:
    common_block = dedent(
        """
        from __future__ import annotations

        import json
        import sys
        from pathlib import Path

        import pandas as pd


        def load_market_data(csv_paths: list[str]) -> pd.DataFrame:
            frames = []
            for csv_path in csv_paths:
                raw = pd.read_csv(csv_path, header=[0, 1])
                if str(raw.iloc[0, 0]).strip().lower() == "date":
                    raw = raw.iloc[1:].reset_index(drop=True)
                raw.columns = pd.MultiIndex.from_tuples([("meta", "Date")] + list(raw.columns[1:]))
                raw[("meta", "Date")] = pd.to_datetime(raw[("meta", "Date")], errors="coerce")
                raw = raw.dropna(subset=[("meta", "Date")])

                ticker_names = []
                for top_level, second_level in raw.columns[1:]:
                    if top_level != "meta" and top_level not in ticker_names:
                        ticker_names.append(top_level)

                for ticker in ticker_names:
                    subset = raw.loc[:, [("meta", "Date")] + [col for col in raw.columns[1:] if col[0] == ticker]].copy()
                    subset.columns = ["Date"] + [col[1] for col in subset.columns[1:]]
                    subset["Ticker"] = ticker
                    frames.append(subset)

            if not frames:
                raise ValueError("No se pudieron cargar series desde los CSV.")

            market = pd.concat(frames, ignore_index=True)
            market = market.sort_values(["Ticker", "Date"]).reset_index(drop=True)
            market["Close"] = pd.to_numeric(market["Close"], errors="coerce")
            market = market.dropna(subset=["Date", "Ticker", "Close"])
            return market


        def summarize_series(market: pd.DataFrame, ticker: str) -> dict:
            series = market.loc[market["Ticker"] == ticker].copy()
            if series.empty:
                raise ValueError(f"No hay datos para {ticker}.")
            series = series.sort_values("Date")
            start_close = float(series["Close"].iloc[0])
            end_close = float(series["Close"].iloc[-1])
            absolute_growth = end_close - start_close
            percentage_growth = (absolute_growth / start_close) * 100 if start_close else 0.0
            return {
                "ticker": ticker,
                "rows": int(len(series)),
                "start_date": series["Date"].iloc[0].strftime("%Y-%m-%d"),
                "end_date": series["Date"].iloc[-1].strftime("%Y-%m-%d"),
                "start_close": start_close,
                "end_close": end_close,
                "absolute_growth": absolute_growth,
                "percentage_growth": percentage_growth,
            }


        def build_asset_overview(market: pd.DataFrame, ticker: str) -> dict:
            series = market.loc[market["Ticker"] == ticker].copy()
            if series.empty:
                raise ValueError(f"No hay datos para {ticker}.")
            series = series.sort_values("Date")
            first_close = float(series["Close"].iloc[0])
            last_close = float(series["Close"].iloc[-1])
            absolute_change = last_close - first_close
            percentage_change = (absolute_change / first_close) * 100 if first_close else 0.0
            return {
                "ticker": ticker,
                "rows": int(len(series)),
                "start_date": series["Date"].iloc[0].strftime("%Y-%m-%d"),
                "end_date": series["Date"].iloc[-1].strftime("%Y-%m-%d"),
                "first_close": first_close,
                "last_close": last_close,
                "absolute_change": absolute_change,
                "percentage_change": percentage_change,
                "min_close": float(series["Close"].min()),
                "max_close": float(series["Close"].max()),
                "average_close": float(series["Close"].mean()),
            }


        def summarize_returns(market: pd.DataFrame, ticker: str) -> dict:
            series = market.loc[market["Ticker"] == ticker].copy()
            if series.empty:
                raise ValueError(f"No hay datos para {ticker}.")
            series = series.sort_values("Date")
            series["daily_return"] = series["Close"].pct_change()
            returns = series["daily_return"].dropna()
            if returns.empty:
                raise ValueError(f"No hay suficientes datos para calcular retornos de {ticker}.")
            cumulative_return = ((series["Close"].iloc[-1] / series["Close"].iloc[0]) - 1) * 100 if float(series["Close"].iloc[0]) else 0.0
            return {
                "ticker": ticker,
                "rows": int(len(series)),
                "start_date": series["Date"].iloc[0].strftime("%Y-%m-%d"),
                "end_date": series["Date"].iloc[-1].strftime("%Y-%m-%d"),
                "mean_daily_return": float(returns.mean() * 100),
                "volatility": float(returns.std(ddof=0) * 100),
                "best_day_return": float(returns.max() * 100),
                "worst_day_return": float(returns.min() * 100),
                "cumulative_return": float(cumulative_return),
            }


        def summarize_risk(market: pd.DataFrame, ticker: str) -> dict:
            series = market.loc[market["Ticker"] == ticker].copy()
            if series.empty:
                raise ValueError(f"No hay datos para {ticker}.")
            series = series.sort_values("Date")
            series["daily_return"] = series["Close"].pct_change()
            returns = series["daily_return"].dropna()
            if returns.empty:
                raise ValueError(f"No hay suficientes datos para calcular riesgo historico de {ticker}.")
            series["cummax_close"] = series["Close"].cummax()
            series["drawdown"] = (series["Close"] / series["cummax_close"]) - 1
            max_drawdown_idx = series["drawdown"].idxmin()
            drawdown_end = series.loc[max_drawdown_idx, "Date"].strftime("%Y-%m-%d")
            return {
                "ticker": ticker,
                "rows": int(len(series)),
                "start_date": series["Date"].iloc[0].strftime("%Y-%m-%d"),
                "end_date": series["Date"].iloc[-1].strftime("%Y-%m-%d"),
                "volatility": float(returns.std(ddof=0) * 100),
                "max_drawdown": float(series["drawdown"].min() * 100),
                "worst_day_return": float(returns.min() * 100),
                "best_day_return": float(returns.max() * 100),
                "drawdown_end": drawdown_end,
            }


        def summarize_technical(market: pd.DataFrame, ticker: str) -> dict:
            series = market.loc[market["Ticker"] == ticker].copy()
            if series.empty:
                raise ValueError(f"No hay datos para {ticker}.")
            series = series.sort_values("Date").copy()
            series["sma_short"] = series["Close"].rolling(window=5, min_periods=5).mean()
            series["sma_long"] = series["Close"].rolling(window=20, min_periods=20).mean()
            delta = series["Close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14, min_periods=14).mean()
            avg_loss = loss.rolling(window=14, min_periods=14).mean()
            rs = avg_gain / avg_loss.replace(0, pd.NA)
            series["rsi_14"] = 100 - (100 / (1 + rs))
            valid = series.dropna(subset=["sma_short", "sma_long", "rsi_14"])
            if valid.empty:
                raise ValueError(f"No hay suficientes datos para calcular analisis tecnico de {ticker}.")
            last = valid.iloc[-1]
            signal = "neutral"
            if float(last["sma_short"]) > float(last["sma_long"]) and float(last["rsi_14"]) < 70:
                signal = "alcista moderada"
            elif float(last["sma_short"]) < float(last["sma_long"]) and float(last["rsi_14"]) > 30:
                signal = "bajista moderada"
            if float(last["rsi_14"]) >= 70:
                signal = "sobrecompra"
            elif float(last["rsi_14"]) <= 30:
                signal = "sobreventa"
            return {
                "ticker": ticker,
                "rows": int(len(series)),
                "start_date": series["Date"].iloc[0].strftime("%Y-%m-%d"),
                "end_date": series["Date"].iloc[-1].strftime("%Y-%m-%d"),
                "last_close": float(last["Close"]),
                "sma_short": float(last["sma_short"]),
                "sma_long": float(last["sma_long"]),
                "rsi_14": float(last["rsi_14"]),
                "signal": signal,
            }
        """
    ).strip()

    body = build_code_body(plan)
    return f"{common_block}\n\n\n{body}\n"
