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


if __name__ == "__main__":
    unittest.main()
