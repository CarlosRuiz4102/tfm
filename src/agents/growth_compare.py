from __future__ import annotations

from textwrap import dedent

from src.agents.base import AgentSpec


def render_price_growth_answer(output: dict) -> str:
    summary = output["summary"]
    return (
        f"{summary['ticker']} paso de {summary['start_close']:.2f} a {summary['end_close']:.2f} "
        f"entre {summary['start_date']} y {summary['end_date']}. "
        f"La variacion absoluta fue {summary['absolute_growth']:.2f} y la variacion porcentual "
        f"fue {summary['percentage_growth']:.2f}%."
    )


def render_compare_assets_answer(output: dict) -> str:
    comparisons = output["comparisons"]
    parts = []
    for item in comparisons:
        parts.append(
            f"{item['ticker']} cambio {item['percentage_growth']:.2f}% "
            f"({item['start_close']:.2f} -> {item['end_close']:.2f})"
        )
    return (
        f"Comparativa completada. {'; '.join(parts)}. "
        f"El mejor comportamiento fue {output['winner']}."
    )


PRICE_GROWTH_AGENT = AgentSpec(
    intent="price_growth",
    agent_name="growth_agent",
    metrics=["start_close", "end_close", "absolute_growth", "percentage_growth"],
    plots=["closing_price_line"],
    required_columns=["Date", "Ticker", "Close"],
    textual_focus="explicar crecimiento absoluto y porcentual del activo en el rango disponible",
    code_body=dedent(
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
    ).strip(),
    render_answer=render_price_growth_answer,
)


COMPARE_ASSETS_AGENT = AgentSpec(
    intent="compare_assets",
    agent_name="compare_agent",
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
    code_body=dedent(
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
    ).strip(),
    render_answer=render_compare_assets_answer,
)
