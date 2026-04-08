from __future__ import annotations

from textwrap import dedent

from src.agents.base import AgentSpec


def render_technical_analysis_answer(output: dict) -> str:
    summary = output["technical_summary"]
    return (
        f"Analisis tecnico completado para {summary['ticker']}. El ultimo cierre fue "
        f"{summary['last_close']:.2f}, la media movil corta {summary['sma_short']:.2f}, "
        f"la media movil larga {summary['sma_long']:.2f} y el RSI(14) {summary['rsi_14']:.2f}. "
        f"La senal tecnica actual es {summary['signal']}."
    )


TECHNICAL_ANALYSIS_AGENT = AgentSpec(
    intent="technical_analysis",
    agent_name="technical_agent",
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
    code_body=dedent(
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
    ).strip(),
    render_answer=render_technical_analysis_answer,
)
