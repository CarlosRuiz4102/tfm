from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.llm.pipeline import _normalize_code_validation_payload
from src.schemas import AnalysisPlan, CodeValidationDecision, FinancialDataRequest, FinancialQueryInput


def _mock_yfinance_output(csv_path: str) -> pd.DataFrame:
    dataframe = pd.read_csv(Path(csv_path), header=[0, 1], index_col=0)
    dataframe.index = pd.to_datetime(dataframe.index)
    dataframe.index.name = "Date"
    return dataframe


class PhaseThreeWorkflowTests(unittest.TestCase):
    """Tests centrados en la validacion y reparacion del codigo generado."""

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

    def _valid_code(self, query_input, plan, input_payload=None):
        return (
            """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = {
        "metrics": {"tickers": payload["tickers"]},
        "summary": "ok",
        "limitations": [],
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
            """.strip(),
            [],
        )

    def test_code_validation_accepts_valid_script_and_continues(self) -> None:
        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=self._fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(self.sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=self._fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=self._valid_code),
            patch(
                "src.graph.nodes.build_llm_code_validation",
                return_value=(
                    CodeValidationDecision(
                        decision="valid",
                        errors=[],
                        warnings=[],
                        required_fixes=[],
                        reasoning="El codigo implementa bien el plan.",
                    ),
                    [],
                ),
            ),
            patch("src.graph.nodes.build_llm_interpretation", return_value=("ok", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed")
        self.assertIsNotNone(state.code_validation_decision)
        self.assertEqual(state.code_validation_decision.decision, "valid")

    def test_code_validation_can_request_repair_and_then_continue(self) -> None:
        observed_feedback: dict[str, str] = {}

        def _repair_code(query_input, plan, previous_code, error_detail, input_payload=None):
            observed_feedback["value"] = error_detail
            return self._valid_code(query_input, plan, input_payload)

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=self._fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(self.sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=self._fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=lambda q, p, input_payload=None: ("print('mal')", [])),
            patch(
                "src.graph.nodes.build_llm_code_validation",
                side_effect=[
                    (
                        CodeValidationDecision(
                            decision="repairable",
                            errors=["La salida no sigue el formato esperado."],
                            warnings=[],
                            required_fixes=["Devolver metrics, summary y limitations."],
                            reasoning="El script parece recuperable.",
                        ),
                        [],
                    ),
                    (
                        CodeValidationDecision(
                            decision="valid",
                            errors=[],
                            warnings=[],
                            required_fixes=[],
                            reasoning="La version corregida ya puede continuar.",
                        ),
                        [],
                    ),
                ],
            ),
            patch("src.graph.nodes.repair_llm_code", side_effect=_repair_code),
            patch("src.graph.nodes.build_llm_interpretation", return_value=("ok", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.code_repair_attempts, 1)
        self.assertIn("required_fixes=", observed_feedback["value"])

    def test_code_validation_can_block_the_flow(self) -> None:
        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=self._fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(self.sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=self._fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=self._valid_code),
            patch(
                "src.graph.nodes.build_llm_code_validation",
                return_value=(
                    CodeValidationDecision(
                        decision="blocked",
                        errors=["El codigo no sigue el plan analitico recibido."],
                        warnings=[],
                        required_fixes=[],
                        reasoning="La desviacion es demasiado grande.",
                    ),
                    [],
                ),
            ),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("Agente 4", state.final_answer)

    def test_code_validation_payload_can_recover_missing_reasoning(self) -> None:
        payload = {
            "decision": "repairable",
            "errors": ["La salida no sigue el formato esperado."],
            "warnings": [],
            "required_fixes": ["Devolver metrics, summary y limitations."],
        }

        normalized = _normalize_code_validation_payload(payload)
        decision = CodeValidationDecision.from_dict(normalized)

        self.assertEqual(decision.decision, "repairable")
        self.assertTrue(decision.reasoning)
        self.assertIn("La salida no sigue el formato esperado.", decision.reasoning)


if __name__ == "__main__":
    unittest.main()
