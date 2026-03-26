from __future__ import annotations

from textwrap import dedent

from src.schemas import AnalysisPlan, FinancialQueryInput


def build_analysis_plan(query_input: FinancialQueryInput) -> AnalysisPlan:
    if query_input.intent == "price_growth":
        return AnalysisPlan(
            intent="price_growth",
            metrics=["start_close", "end_close", "absolute_growth", "percentage_growth"],
            plots=["closing_price_line"],
            required_columns=["Date", "Ticker", "Close"],
            textual_focus="explicar crecimiento absoluto y porcentual del activo en el rango disponible",
            agent_name="growth_agent",
        )
    if query_input.intent == "compare_assets":
        return AnalysisPlan(
            intent="compare_assets",
            metrics=[
                "start_close",
                "end_close",
                "percentage_growth",
                "normalized_last_value",
                "winner_by_growth",
            ],
            plots=["normalized_performance_line"],
            required_columns=["Date", "Ticker", "Close"],
            textual_focus="comparar rendimiento relativo y destacar el activo con mejor comportamiento",
            agent_name="compare_agent",
        )
    if query_input.intent == "asset_overview":
        return AnalysisPlan(
            intent="asset_overview",
            metrics=[
                "first_close",
                "last_close",
                "absolute_change",
                "percentage_change",
                "min_close",
                "max_close",
                "average_close",
            ],
            plots=["closing_price_line"],
            required_columns=["Date", "Ticker", "Close"],
            textual_focus="resumir el comportamiento general del activo y sus niveles de precio mas representativos",
            agent_name="overview_agent",
        )
    if query_input.intent == "return_analysis":
        return AnalysisPlan(
            intent="return_analysis",
            metrics=[
                "mean_daily_return",
                "volatility",
                "best_day_return",
                "worst_day_return",
                "cumulative_return",
            ],
            plots=["daily_returns_distribution", "cumulative_return_line"],
            required_columns=["Date", "Ticker", "Close"],
            textual_focus="analizar la serie de retornos historicos y destacar rentabilidad acumulada, volatilidad y extremos",
            agent_name="returns_agent",
        )
    if query_input.intent == "historical_risk_analysis":
        return AnalysisPlan(
            intent="historical_risk_analysis",
            metrics=[
                "volatility",
                "max_drawdown",
                "worst_day_return",
                "best_day_return",
                "drawdown_end",
            ],
            plots=["drawdown_line", "rolling_volatility_line"],
            required_columns=["Date", "Ticker", "Close"],
            textual_focus="evaluar el riesgo historico mediante volatilidad, drawdown maximo y extremos diarios",
            agent_name="risk_agent",
        )
    if query_input.intent == "technical_analysis":
        return AnalysisPlan(
            intent="technical_analysis",
            metrics=[
                "last_close",
                "sma_short",
                "sma_long",
                "rsi_14",
                "signal",
            ],
            plots=["close_with_moving_averages", "rsi_line"],
            required_columns=["Date", "Ticker", "Close"],
            textual_focus="identificar senales tecnicas simples con medias moviles y RSI",
            agent_name="technical_agent",
        )
    raise ValueError(f"Intent no soportada en el MVP: {query_input.intent}")


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

    if plan.intent == "price_growth":
        body = dedent(
            """
            def main() -> int:
                payload_path = Path(sys.argv[1])
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
                market = load_market_data(payload["csv_paths"])
                ticker = payload["tickers"][0]
                summary = summarize_series(market, ticker)
                output = {
                    "intent": "price_growth",
                    "ticker": ticker,
                    "summary": summary,
                    "textual_focus": payload["analysis_plan"]["textual_focus"],
                }
                print(json.dumps(output, ensure_ascii=False))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
    elif plan.intent == "compare_assets":
        body = dedent(
            """
            def main() -> int:
                payload_path = Path(sys.argv[1])
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
                market = load_market_data(payload["csv_paths"])

                comparisons = [summarize_series(market, ticker) for ticker in payload["tickers"]]
                winner = max(comparisons, key=lambda item: item["percentage_growth"])
                output = {
                    "intent": "compare_assets",
                    "comparisons": comparisons,
                    "winner": winner["ticker"],
                    "textual_focus": payload["analysis_plan"]["textual_focus"],
                }
                print(json.dumps(output, ensure_ascii=False))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
    elif plan.intent == "asset_overview":
        body = dedent(
            """
            def main() -> int:
                payload_path = Path(sys.argv[1])
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
                market = load_market_data(payload["csv_paths"])
                ticker = payload["tickers"][0]
                overview = build_asset_overview(market, ticker)
                output = {
                    "intent": "asset_overview",
                    "ticker": ticker,
                    "overview": overview,
                    "textual_focus": payload["analysis_plan"]["textual_focus"],
                }
                print(json.dumps(output, ensure_ascii=False))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
    elif plan.intent == "return_analysis":
        body = dedent(
            """
            def main() -> int:
                payload_path = Path(sys.argv[1])
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
                market = load_market_data(payload["csv_paths"])
                summaries = [summarize_returns(market, ticker) for ticker in payload["tickers"]]
                best = max(summaries, key=lambda item: item["cumulative_return"])
                output = {
                    "intent": "return_analysis",
                    "returns_summary": summaries,
                    "best_ticker_by_cumulative_return": best["ticker"],
                    "textual_focus": payload["analysis_plan"]["textual_focus"],
                }
                print(json.dumps(output, ensure_ascii=False))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
    elif plan.intent == "historical_risk_analysis":
        body = dedent(
            """
            def main() -> int:
                payload_path = Path(sys.argv[1])
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
                market = load_market_data(payload["csv_paths"])
                summaries = [summarize_risk(market, ticker) for ticker in payload["tickers"]]
                highest_risk = max(summaries, key=lambda item: abs(item["max_drawdown"]))
                output = {
                    "intent": "historical_risk_analysis",
                    "risk_summary": summaries,
                    "highest_risk_ticker": highest_risk["ticker"],
                    "textual_focus": payload["analysis_plan"]["textual_focus"],
                }
                print(json.dumps(output, ensure_ascii=False))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
    elif plan.intent == "technical_analysis":
        body = dedent(
            """
            def main() -> int:
                payload_path = Path(sys.argv[1])
                payload = json.loads(payload_path.read_text(encoding="utf-8"))
                market = load_market_data(payload["csv_paths"])
                ticker = payload["tickers"][0]
                technical_summary = summarize_technical(market, ticker)
                output = {
                    "intent": "technical_analysis",
                    "ticker": ticker,
                    "technical_summary": technical_summary,
                    "textual_focus": payload["analysis_plan"]["textual_focus"],
                }
                print(json.dumps(output, ensure_ascii=False))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
    else:
        raise ValueError(f"No existe plantilla de codigo para la intent {plan.intent}.")

    return f"{common_block}\n\n\n{body}\n"
