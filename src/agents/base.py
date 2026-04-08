from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.schemas import AnalysisPlan


AnswerRenderer = Callable[[dict], str]


@dataclass(frozen=True)
class AgentSpec:
    intent: str
    agent_name: str
    metrics: list[str]
    plots: list[str]
    required_columns: list[str]
    textual_focus: str
    code_body: str
    render_answer: AnswerRenderer

    def build_plan(self) -> AnalysisPlan:
        return AnalysisPlan(
            intent=self.intent,
            metrics=list(self.metrics),
            plots=list(self.plots),
            required_columns=list(self.required_columns),
            textual_focus=self.textual_focus,
            agent_name=self.agent_name,
        )
