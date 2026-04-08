from __future__ import annotations

from textwrap import dedent

from src.agents.base import AgentSpec


def render_return_analysis_answer(output: dict) -> str:
    summaries = output["returns_summary"]
    parts = []
    for item in summaries:
        parts.append(
            f"{item['ticker']} retorno acumulado {item['cumulative_return']:.2f}%, "
            f"media diaria {item['mean_daily_return']:.3f}% y volatilidad {item['volatility']:.3f}%"
        )
    return (
        f"Analisis de retornos completado. {'; '.join(parts)}. "
        f"El mejor retorno acumulado fue {output['best_ticker_by_cumulative_return']}."
    )


RETURN_ANALYSIS_AGENT = AgentSpec(
    intent="return_analysis",
    agent_name="returns_agent",
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
    code_body=dedent(
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
    ).strip(),
    render_answer=render_return_analysis_answer,
)
