from __future__ import annotations

from textwrap import dedent

from src.agents.base import AgentSpec


def render_asset_overview_answer(output: dict) -> str:
    overview = output["overview"]
    return (
        f"{overview['ticker']} presenta {overview['rows']} registros entre {overview['start_date']} "
        f"y {overview['end_date']}. El cierre paso de {overview['first_close']:.2f} a "
        f"{overview['last_close']:.2f}, con un cambio de {overview['absolute_change']:.2f} "
        f"({overview['percentage_change']:.2f}%). En el periodo, el minimo fue {overview['min_close']:.2f}, "
        f"el maximo {overview['max_close']:.2f} y la media de cierre {overview['average_close']:.2f}."
    )


ASSET_OVERVIEW_AGENT = AgentSpec(
    intent="asset_overview",
    agent_name="overview_agent",
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
    code_body=dedent(
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
    ).strip(),
    render_answer=render_asset_overview_answer,
)
