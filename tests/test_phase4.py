from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.graph.nodes import interpretation_node
from src.schemas import AnalysisPlan, CodeValidationDecision, FinancialDataRequest, FinancialQueryInput, WorkflowState


def _mock_yfinance_output(csv_path: str) -> pd.DataFrame:
    """Reutiliza CSVs congelados para evitar dependencias de red en los tests."""
    dataframe = pd.read_csv(Path(csv_path), header=[0, 1], index_col=0)
    dataframe.index = pd.to_datetime(dataframe.index)
    dataframe.index.name = "Date"
    return dataframe


def _valid_runtime_script(summary: str = "ok") -> str:
    return f"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = {{
        "metrics": {{"tickers": payload["tickers"], "csv_count": len(payload["csv_paths"])}},
        "summary": "{summary}",
        "limitations": [],
    }}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
    """.strip()


def _failing_runtime_script() -> str:
    return """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raise KeyError(payload["tickers"][0])


if __name__ == "__main__":
    main()
    """.strip()


class PhaseFourWorkflowTests(unittest.TestCase):
    """Tests centrados en la parte 4: ejecucion, reparacion y bloqueo."""

    def setUp(self) -> None:
        self.workflow = build_workflow()
        self.sample = SAMPLE_INPUTS["overview_aapl"]

    def _fake_data_request(self, query_input):
        return (
            FinancialDataRequest.from_dict(
                {
                    "user_query": query_input.query,
                    "provider": "yfinance",
                    "instruments": [{"ticker": "AAPL"}],
                    "interval": "1d",
                    "start": None,
                    "end": None,
                    "period": "3mo",
                    "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
                    "needs_clarification": False,
                    "clarification_reason": None,
                }
            ),
            [],
        )

    def _fake_analysis(self, query_input, input_payload=None):
        return (
            AnalysisPlan(
                analytical_goal="Describir AAPL en 3 meses.",
                analysis_type="historical_overview",
                metrics=["ultimo_cierre"],
                required_columns=["Date", "Close"],
                data_requirements=["CSV historico normalizado"],
                output_requirements=["JSON con metrics, summary y limitations"],
                presentation_preferences=["respuesta breve"],
                reasoning="La consulta pide una vision general simple.",
            ),
            [],
        )

    def _code_validator_ok(self):
        return (
            CodeValidationDecision(
                decision="valid",
                errors=[],
                warnings=[],
                required_fixes=[],
                reasoning="El codigo puede continuar.",
            ),
            [],
        )

    def test_execution_payload_no_longer_includes_analysis_plan(self) -> None:
        script_without_plan_dependency = """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "analysis_plan" in payload:
        raise AssertionError("analysis_plan no debe llegar a la parte 4")
    if "input" in payload:
        raise AssertionError("input no debe duplicarse en el payload compacto")
    output = {
        "metrics": {"tickers": payload["tickers"]},
        "summary": "payload correcto",
        "limitations": [],
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
        """.strip()

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=self._fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(self.sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=self._fake_analysis),
            patch("src.graph.nodes.build_llm_code", return_value=(script_without_plan_dependency, [])),
            patch("src.graph.nodes.build_llm_code_validation", return_value=self._code_validator_ok()),
            patch("src.graph.nodes.build_llm_interpretation", return_value=("ok", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.execution_attempts, 1)
        self.assertIsNotNone(state.execution_output)
        self.assertEqual(state.execution_output["summary"], "payload correcto")

    def test_execution_repair_can_recover_after_runtime_failure(self) -> None:
        observed_feedback: dict[str, str] = {}

        def _repair_execution(query_input, previous_code, error_detail, input_payload=None):
            observed_feedback["value"] = error_detail
            return _valid_runtime_script(summary="reparado"), ["Se reparo codigo tras un error de ejecucion."]

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=self._fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(self.sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=self._fake_analysis),
            patch("src.graph.nodes.build_llm_code", return_value=(_failing_runtime_script(), [])),
            patch("src.graph.nodes.build_llm_code_validation", return_value=self._code_validator_ok()),
            patch("src.graph.nodes.repair_llm_execution_code", side_effect=_repair_execution),
            patch("src.graph.nodes.build_llm_interpretation", return_value=("ok", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.execution_attempts, 2)
        self.assertEqual(state.execution_repair_attempts, 1)
        self.assertIsNotNone(state.execution_validation_decision)
        self.assertEqual(state.execution_validation_decision.decision, "valid")
        self.assertIn("returncode=1", observed_feedback["value"])
        self.assertIn("stderr=", observed_feedback["value"])

    def test_execution_blocks_after_exhausting_attempts(self) -> None:
        def _repair_execution(query_input, previous_code, error_detail, input_payload=None):
            return _failing_runtime_script(), ["Se reparo codigo tras un error de ejecucion."]

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=self._fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(self.sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=self._fake_analysis),
            patch("src.graph.nodes.build_llm_code", return_value=(_failing_runtime_script(), [])),
            patch("src.graph.nodes.build_llm_code_validation", return_value=self._code_validator_ok()),
            patch("src.graph.nodes.repair_llm_execution_code", side_effect=_repair_execution),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed_with_error")
        self.assertEqual(state.execution_attempts, 3)
        self.assertEqual(state.execution_repair_attempts, 2)
        self.assertIsNotNone(state.execution_validation_decision)
        self.assertEqual(state.execution_validation_decision.decision, "blocked")
        self.assertIn("Se agotaron los intentos maximos de ejecucion", state.final_answer)

    def test_interpretation_no_longer_depends_on_analysis_plan_or_analysis_hints(self) -> None:
        observed_payload: dict[str, object] = {}
        state = WorkflowState.from_input(FinancialQueryInput(query="Compara Nvidia y AMD en 2 anos"))
        state.normalized_query.tickers = ["NVDA", "AMD"]
        state.normalized_query.period = "2y"
        state.normalized_query.interval = "1d"
        state.execution_returncode = 0
        state.execution_output = {
            "analysis_type": "comparative_return_analysis",
            "analysis_level": "C",
            "metrics": {"retorno_total": {"NVDA": 10.0, "AMD": 5.0}},
            "summary": "NVDA rindio mejor.",
            "limitations": [],
        }

        def _fake_interpretation(payload: dict) -> tuple[str, list[str]]:
            observed_payload.update(payload)
            return "ok", []

        with patch("src.graph.nodes.build_llm_interpretation", side_effect=_fake_interpretation):
            interpreted = interpretation_node(state)

        self.assertEqual(interpreted.status, "completed")
        self.assertEqual(interpreted.final_answer, "ok")
        self.assertEqual(observed_payload["user_query"], "Compara Nvidia y AMD en 2 anos")
        self.assertIn("execution_output", observed_payload)
        self.assertNotIn("analysis_plan", observed_payload)
        self.assertNotIn("analysis_type", observed_payload["execution_output"])
        self.assertNotIn("analysis_level", observed_payload["execution_output"])


if __name__ == "__main__":
    unittest.main()
