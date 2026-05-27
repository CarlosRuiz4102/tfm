from __future__ import annotations

import unittest
from unittest.mock import patch

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import AnalysisPlan, FinancialQueryInput


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = build_workflow()

    def invoke_with_llm_answer(self, example_name: str):
        def _fake_analysis(query_input):
            return (
                AnalysisPlan(
                    interpreted_intent=query_input.intent or "financial_analysis",
                    analysis_type=query_input.intent or "financial_analysis",
                    metrics=["rows"],
                    required_columns=["Date", "Close"],
                    data_requirements=["CSV historico"],
                    output_requirements=["JSON con metricas y resumen"],
                    presentation_preferences=["resumen breve"],
                    reasoning="Analisis simulado para tests.",
                ),
                [],
            )

        def _fake_code(query_input, plan):
            return (
                """
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    tickers = payload["tickers"]
    output = {
        "analysis_type": payload["analysis_plan"]["analysis_type"],
        "metrics": {"tickers": tickers, "csv_count": len(payload["csv_paths"])},
        "summary": f"Analisis completado para {', '.join(tickers)}",
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
                """.strip(),
                [],
            )

        def _fake_interpretation(output: dict, plan) -> tuple[str, list[str]]:
            return f"Respuesta LLM: {output['summary']}", []

        with (
            patch("src.graph.nodes.build_llm_analysis", side_effect=_fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=_fake_code),
            patch("src.graph.nodes.build_llm_interpretation", side_effect=_fake_interpretation),
        ):
            return self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS[example_name]))

    def test_growth_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("growth_nvda")
        self.assertEqual(state.status, "completed")
        self.assertIn("NVDA", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_compare_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("compare_nvda_amd")
        self.assertEqual(state.status, "completed")
        self.assertIn("NVDA", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_asset_overview_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("overview_aapl")
        self.assertEqual(state.status, "completed")
        self.assertIn("AAPL", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_return_analysis_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("returns_qqq_spy")
        self.assertEqual(state.status, "completed")
        self.assertIn("QQQ", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_historical_risk_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("risk_qqq_spy")
        self.assertEqual(state.status, "completed")
        self.assertIn("QQQ", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_technical_analysis_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("technical_aapl")
        self.assertEqual(state.status, "completed")
        self.assertIn("AAPL", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_missing_llm_configuration_returns_error(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["growth_nvda"]))

        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("Falta configurar LLM_API_KEY/LLM_MODEL", state.final_answer)

    def test_invalid_start_date_returns_error(self) -> None:
        payload = dict(SAMPLE_INPUTS["growth_nvda"])
        payload["start"] = "17/03/2021"
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("formato YYYY-MM-DD", state.final_answer)

    def test_missing_csv_returns_error(self) -> None:
        payload = dict(SAMPLE_INPUTS["growth_nvda"])
        payload["csv_paths"] = [r"C:\Users\usuario\Desktop\tfm\data\raw\missing_file.csv"]
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("No existe el CSV", state.final_answer)

    def test_empty_query_returns_error(self) -> None:
        payload = dict(SAMPLE_INPUTS["technical_aapl"])
        payload["query"] = ""
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("query no puede estar vacia", state.final_answer)


if __name__ == "__main__":
    unittest.main()
