from __future__ import annotations

import unittest

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = build_workflow()

    def test_growth_example_completes(self) -> None:
        state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["growth_nvda"]))
        self.assertEqual(state.status, "completed")
        self.assertIn("NVDA", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_compare_example_completes(self) -> None:
        state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["compare_nvda_amd"]))
        self.assertEqual(state.status, "completed")
        self.assertIn("Comparativa completada", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_asset_overview_example_completes(self) -> None:
        state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["overview_aapl"]))
        self.assertEqual(state.status, "completed")
        self.assertIn("AAPL", state.final_answer)
        self.assertIn("media de cierre", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_return_analysis_example_completes(self) -> None:
        state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["returns_qqq_spy"]))
        self.assertEqual(state.status, "completed")
        self.assertIn("Analisis de retornos completado", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_historical_risk_example_completes(self) -> None:
        state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["risk_qqq_spy"]))
        self.assertEqual(state.status, "completed")
        self.assertIn("Analisis de riesgo historico completado", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_technical_analysis_example_completes(self) -> None:
        state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["technical_aapl"]))
        self.assertEqual(state.status, "completed")
        self.assertIn("Analisis tecnico completado", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)

    def test_invalid_intent_returns_error(self) -> None:
        payload = dict(SAMPLE_INPUTS["growth_nvda"])
        payload["intent"] = "unsupported_intent"
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("no esta soportada", state.final_answer)

    def test_missing_csv_returns_error(self) -> None:
        payload = dict(SAMPLE_INPUTS["growth_nvda"])
        payload["csv_paths"] = [r"C:\Users\usuario\Desktop\tfm\data\raw\missing_file.csv"]
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("No existe el CSV", state.final_answer)

    def test_technical_analysis_requires_one_ticker(self) -> None:
        payload = dict(SAMPLE_INPUTS["technical_aapl"])
        payload["tickers"] = ["AAPL", "MSFT"]
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("technical_analysis requiere exactamente 1 ticker", state.final_answer)


if __name__ == "__main__":
    unittest.main()
