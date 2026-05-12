from __future__ import annotations

from textwrap import dedent

from src.agents.base import AgentSpec


def render_historical_risk_answer(output: dict) -> str:
    summaries = output["risk_summary"]
    parts = []
    for item in summaries:
        parts.append(
            f"{item['ticker']} volatilidad {item['volatility']:.3f}%, "
            f"drawdown maximo {item['max_drawdown']:.2f}% y peor dia {item['worst_day_return']:.2f}%"
        )
    return (
        f"Analisis de riesgo historico completado. {'; '.join(parts)}. "
        f"El activo con mayor drawdown observado fue {output['highest_risk_ticker']}."
    )


HISTORICAL_RISK_AGENT = AgentSpec(
    intent="historical_risk_analysis",
    agent_name="risk_agent",
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
    code_body=dedent(
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
    ).strip(),
    render_answer=render_historical_risk_answer,
)
