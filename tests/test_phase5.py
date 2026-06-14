from __future__ import annotations

import unittest
from unittest.mock import patch

from src.graph.nodes import _build_interpretation_payload, interpretation_node
from src.llm.prompts import build_interpretation_messages
from src.schemas import FinancialQueryInput, WorkflowState


class PhaseFiveInterpretationTests(unittest.TestCase):
    """Tests centrados en la parte 5: payload, aislamiento y respuesta final."""

    def test_interpretation_payload_removes_analysis_hints_and_preserves_context(self) -> None:
        state = WorkflowState.from_input(FinancialQueryInput(query="Compara Nvidia y AMD en 2 anos"))
        state.normalized_query.tickers = ["NVDA", "AMD"]
        state.normalized_query.period = "2y"
        state.normalized_query.interval = "1d"
        state.warnings = ["La ejecucion produjo stderr no vacio pese a terminar con returncode 0."]
        state.execution_output = {
            "analysis_type": "comparative_return_analysis",
            "analysis_level": "C",
            "presentation_preferences": ["respuesta estructurada"],
            "metrics": {"retorno_total": {"NVDA": 10.0, "AMD": 5.0}},
            "summary": "NVDA rindio mejor.",
            "limitations": [],
        }

        payload = _build_interpretation_payload(state)

        self.assertEqual(payload["user_query"], "Compara Nvidia y AMD en 2 anos")
        self.assertEqual(payload["resolved_context"]["tickers"], ["NVDA", "AMD"])
        self.assertEqual(payload["resolved_context"]["temporal_context"]["period"], "2y")
        self.assertEqual(payload["warnings"], state.warnings)
        self.assertNotIn("analysis_type", payload["execution_output"])
        self.assertNotIn("analysis_level", payload["execution_output"])
        self.assertNotIn("presentation_preferences", payload["execution_output"])
        self.assertIn("metrics", payload["execution_output"])
        self.assertIn("summary", payload["execution_output"])
        self.assertIn("limitations", payload["execution_output"])

    def test_interpretation_node_stores_payload_and_works_without_analysis_plan(self) -> None:
        observed_payload: dict[str, object] = {}
        state = WorkflowState.from_input(FinancialQueryInput(query="Dame una vision general de AAPL en 3 meses"))
        state.normalized_query.tickers = ["AAPL"]
        state.normalized_query.period = "3mo"
        state.normalized_query.interval = "1d"
        state.execution_returncode = 0
        state.execution_output = {
            "metrics": {"ultimo_cierre": 123.45},
            "summary": "AAPL termino el periodo con un cierre superior al inicio.",
            "limitations": [],
        }

        def _fake_interpretation(payload: dict) -> tuple[str, list[str]]:
            observed_payload.update(payload)
            return "Respuesta final simulada.", []

        with patch("src.graph.nodes.build_llm_interpretation", side_effect=_fake_interpretation):
            interpreted = interpretation_node(state)

        self.assertEqual(interpreted.status, "completed")
        self.assertEqual(interpreted.final_answer, "Respuesta final simulada.")
        self.assertIsNotNone(interpreted.interpretation_payload)
        self.assertEqual(interpreted.interpretation_payload, observed_payload)
        self.assertNotIn("analysis_plan", observed_payload)

    def test_interpretation_prompt_does_not_reference_analysis_plan(self) -> None:
        payload = {
            "user_query": "Cuanto ha subido Nvidia en 5 anos",
            "resolved_context": {"tickers": ["NVDA"], "temporal_context": {"period": "5y", "interval": "1d"}},
            "execution_output": {"metrics": {"retorno_total": 1273.33}, "summary": "ok", "limitations": []},
            "warnings": [],
        }

        messages = build_interpretation_messages(payload)
        joined = "\n".join(message.content for message in messages)

        self.assertIn("execution_output", joined)
        self.assertNotIn("analysis_plan", joined)
        self.assertNotIn("analysis_type", joined)


if __name__ == "__main__":
    unittest.main()
