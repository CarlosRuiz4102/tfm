from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import AnalysisPlan, FinancialDataRequest, FinancialQueryInput


def _mock_yfinance_output(csv_path: str) -> pd.DataFrame:
    """Reutiliza CSV congelados para simular una respuesta real de yfinance."""
    dataframe = pd.read_csv(Path(csv_path), header=[0, 1], index_col=0)
    dataframe.index = pd.to_datetime(dataframe.index)
    dataframe.index.name = "Date"
    return dataframe


class PhaseTwoWorkflowTests(unittest.TestCase):
    """Tests centrados en la conexion entre la fase de datos y la fase 2."""

    def setUp(self) -> None:
        self.workflow = build_workflow()

    def test_phase2_receives_explicit_handoff_from_data_phase(self) -> None:
        sample = SAMPLE_INPUTS["overview_aapl"]
        observed_payloads: dict[str, dict] = {}

        def _fake_data_request(query_input):
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

        def _fake_analysis(query_input, input_payload=None):
            # El analista debe ver el traspaso explicito de la fase 1, no solo
            # query + tickers. Esta es la conexion nueva que queremos preservar.
            self.assertIsNotNone(input_payload)
            self.assertIn("temporal_context", input_payload)
            self.assertIn("data_context", input_payload)
            self.assertEqual(input_payload["tickers"], ["AAPL"])
            self.assertEqual(input_payload["temporal_context"]["period"], "3mo")
            self.assertIn("Close", input_payload["data_context"]["available_columns"])
            observed_payloads["analysis"] = input_payload
            return (
                AnalysisPlan(
                    analytical_goal="Describir el comportamiento historico reciente de AAPL.",
                    analysis_type="historical_overview",
                    metrics=["ultimo_cierre", "variacion_total"],
                    required_columns=["Date", "Close"],
                    data_requirements=["Usar el CSV normalizado descargado para AAPL."],
                    output_requirements=["JSON con metrics, summary y limitations."],
                    presentation_preferences=["Resumen breve y prudente."],
                    reasoning="La consulta pide una vision general breve de un solo activo.",
                ),
                [],
            )

        def _fake_code(query_input, plan, input_payload=None):
            # El generador debe heredar el mismo traspaso de fase 1 que vio el
            # analista para que ambos agentes trabajen sobre el mismo contexto.
            self.assertIsNotNone(input_payload)
            self.assertIn("temporal_context", input_payload)
            self.assertIn("data_context", input_payload)
            self.assertTrue(input_payload["csv_paths"])
            observed_payloads["codegen"] = input_payload
            return (
                """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = {
        "analysis_type": payload["analysis_plan"]["analysis_type"],
        "metrics": {
            "tickers": payload["tickers"],
            "row_count": payload["input"]["data_context"]["row_count"],
        },
        "summary": "Analisis completado para AAPL.",
        "limitations": [],
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
                """.strip(),
                [],
            )

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=_fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=_fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=_fake_code),
            patch("src.graph.nodes.build_llm_interpretation", return_value=("ok", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(sample))

        self.assertEqual(state.status, "completed")
        self.assertIn("analysis", observed_payloads)
        self.assertIn("codegen", observed_payloads)
        self.assertEqual(observed_payloads["analysis"]["data_context"]["row_count"], 60)
        self.assertEqual(observed_payloads["codegen"]["temporal_context"]["interval"], "1d")

    def test_invalid_analysis_plan_stops_before_codegen(self) -> None:
        sample = SAMPLE_INPUTS["overview_aapl"]

        def _fake_data_request(query_input):
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

        def _invalid_analysis(query_input, input_payload=None):
            # Este plan parece correcto de forma superficial, pero pide una
            # columna que no existe en la descarga normalizada de la fase 1.
            return (
                AnalysisPlan(
                    analytical_goal="Analizar AAPL.",
                    analysis_type="historical_overview",
                    metrics=["ultimo_cierre"],
                    required_columns=["NoExiste"],
                    data_requirements=["Usar el CSV normalizado de AAPL."],
                    output_requirements=["JSON con metrics, summary y limitations."],
                    presentation_preferences=["Breve."],
                    reasoning="Prueba negativa para validar el plan.",
                ),
                [],
            )

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=_fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=_invalid_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=AssertionError("No deberia llamarse al codegen.")),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(sample))

        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("AnalysisPlan invalido", state.final_answer)
        self.assertIn("NoExiste", state.final_answer)


if __name__ == "__main__":
    unittest.main()
