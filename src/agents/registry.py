from __future__ import annotations

from src.agents.base import AgentSpec
from src.agents.descriptive import ASSET_OVERVIEW_AGENT
from src.agents.growth_compare import COMPARE_ASSETS_AGENT, PRICE_GROWTH_AGENT
from src.agents.returns import RETURN_ANALYSIS_AGENT
from src.agents.risk import HISTORICAL_RISK_AGENT
from src.agents.technical import TECHNICAL_ANALYSIS_AGENT
from src.schemas import AnalysisPlan, FinancialQueryInput


AGENTS: tuple[AgentSpec, ...] = (
    PRICE_GROWTH_AGENT,
    COMPARE_ASSETS_AGENT,
    ASSET_OVERVIEW_AGENT,
    RETURN_ANALYSIS_AGENT,
    HISTORICAL_RISK_AGENT,
    TECHNICAL_ANALYSIS_AGENT,
)

AGENTS_BY_INTENT: dict[str, AgentSpec] = {agent.intent: agent for agent in AGENTS}


def get_agent_for_intent(intent: str) -> AgentSpec:
    try:
        return AGENTS_BY_INTENT[intent]
    except KeyError as exc:
        raise ValueError(f"Intent no soportada en el MVP: {intent}") from exc


def build_analysis_plan(query_input: FinancialQueryInput) -> AnalysisPlan:
    return get_agent_for_intent(query_input.intent).build_plan()


def build_code_body(plan: AnalysisPlan) -> str:
    return get_agent_for_intent(plan.intent).code_body


def interpret_agent_output(output: dict) -> str:
    intent = output.get("intent")
    if not intent:
        return "La ejecucion termino, pero no se pudo interpretar la salida."
    return get_agent_for_intent(intent).render_answer(output)


def agent_name_by_intent() -> dict[str, str]:
    return {agent.intent: agent.agent_name for agent in AGENTS}
