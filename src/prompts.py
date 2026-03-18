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
                    subset = raw.loc[:, [( "meta", "Date")] + [col for col in raw.columns[1:] if col[0] == ticker]].copy()
                    subset.columns = ["Date"] + [col[1] for col in subset.columns[1:]]
                    subset["Ticker"] = ticker
                    frames.append(subset)

            if not frames:
                raise ValueError("No se pudieron cargar series desde los CSV.")

            market = pd.concat(frames, ignore_index=True)
            market = market.sort_values(["Ticker", "Date"]).reset_index(drop=True)
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
    else:
        raise ValueError(f"No existe plantilla de codigo para la intent {plan.intent}.")

    return f"{common_block}\n\n\n{body}\n"
