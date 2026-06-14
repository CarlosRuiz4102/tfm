from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import AnalysisPlan, CodeValidationDecision, FinancialDataRequest, FinancialQueryInput


def _mock_yfinance_output(csv_path: str) -> pd.DataFrame:
    # Reutilizamos CSVs ya guardados en el proyecto para simular respuestas
    # reales de yfinance sin depender de red durante los tests.
    dataframe = pd.read_csv(Path(csv_path), header=[0, 1], index_col=0)
    dataframe.index = pd.to_datetime(dataframe.index)
    dataframe.index.name = "Date"
    return dataframe


class WorkflowTests(unittest.TestCase):
    """Tests end-to-end del flujo MVP con foco en la nueva fase de datos."""

    def setUp(self) -> None:
        self.workflow = build_workflow()

    def invoke_with_llm_answer(self, example_name: str):
        # Este helper monta un recorrido feliz completo simulando:
        # - Agente 1: genera FinancialDataRequest
        # - Agente 2: genera AnalysisPlan
        # - Agente 3: genera codigo Python
        # - Agente 5: redacta la respuesta final
        sample = SAMPLE_INPUTS[example_name]

        def _fake_data_request(query_input):
            return (
                FinancialDataRequest.from_dict(
                    {
                        "user_query": query_input.query,
                        "provider": "yfinance",
                        "instruments": [{"ticker": ticker} for ticker in sample["tickers"]],
                        "interval": sample["interval"] or "1d",
                        "start": sample.get("start"),
                        "end": sample.get("end"),
                        "period": sample.get("period"),
                        "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
                        "needs_clarification": False,
                        "clarification_reason": None,
                    }
                ),
                [],
            )

        def _fake_analysis(query_input, input_payload=None):
            return (
                AnalysisPlan(
                    analytical_goal=f"Analizar historicamente: {query_input.query}",
                    analysis_type="historical_overview",
                    metrics=["rows"],
                    required_columns=["Date", "Close"],
                    data_requirements=["CSV historico normalizado"],
                    output_requirements=["JSON con metricas y resumen"],
                    presentation_preferences=["resumen breve"],
                    reasoning="Analisis simulado para tests.",
                ),
                [],
            )

        def _fake_code(query_input, plan, input_payload=None):
            # El codigo generado se mantiene intencionalmente simple porque
            # aqui queremos probar la orquestacion, no la calidad analitica.
            return (
                """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    tickers = payload["tickers"]
    output = {
        "analysis_type": "historical_overview",
        "metrics": {"tickers": tickers, "csv_count": len(payload["csv_paths"])},
        "summary": f"Analisis completado para {', '.join(tickers)}",
        "limitations": ["Salida simulada para pruebas automatizadas."],
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
                """.strip(),
                [],
            )

        def _fake_interpretation(payload: dict) -> tuple[str, list[str]]:
            return f"Respuesta LLM: {payload['execution_output']['summary']}", []

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=_fake_data_request),
            patch("src.graph.nodes.download_market_data", return_value=_mock_yfinance_output(sample["csv_paths"][0])),
            patch("src.graph.nodes.build_llm_analysis", side_effect=_fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=_fake_code),
            patch(
                "src.graph.nodes.build_llm_code_validation",
                return_value=(
                    CodeValidationDecision(
                        decision="valid",
                        errors=[],
                        warnings=[],
                        required_fixes=[],
                        reasoning="El codigo puede continuar.",
                    ),
                    [],
                ),
            ),
            patch("src.graph.nodes.build_llm_interpretation", side_effect=_fake_interpretation),
        ):
            return self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS[example_name]))

    def test_growth_example_completes(self) -> None:
        state = self.invoke_with_llm_answer("growth_nvda")
        self.assertEqual(state.status, "completed")
        self.assertIn("NVDA", state.final_answer)
        self.assertEqual(state.execution_returncode, 0)
        self.assertTrue(state.csv_paths)

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
        # Si no hay credenciales, el sistema debe terminar de forma controlada
        # explicando que no puede construir el request con el LLM.
        with patch.dict("os.environ", {}, clear=True):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(SAMPLE_INPUTS["growth_nvda"]))

        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("FinancialDataRequest", state.final_answer)

    def test_query_input_ignores_future_flow_fields(self) -> None:
        payload = dict(SAMPLE_INPUTS["growth_nvda"])
        payload["start"] = "17/03/2021"
        query_input = FinancialQueryInput.from_dict(payload)

        # start ya no pertenece a la entrada inicial; el sistema conserva solo
        # la consulta libre y deja el resto a la fase de datos.
        self.assertEqual(query_input.to_dict(), {"query": payload["query"]})

    def test_empty_query_returns_error(self) -> None:
        payload = dict(SAMPLE_INPUTS["technical_aapl"])
        payload["query"] = ""
        state = self.workflow.invoke(FinancialQueryInput.from_dict(payload))
        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("query no puede estar vacia", state.final_answer)

    def test_blocked_request_stops_data_phase(self) -> None:
        # Un caso bloqueado representa una consulta donde ni siquiera tiene
        # sentido inventar el request porque faltan datos esenciales.
        def _blocked_data_request(query_input):
            return (
                FinancialDataRequest.from_dict(
                    {
                        "user_query": query_input.query,
                        "provider": "yfinance",
                        "instruments": [],
                        "interval": "1d",
                        "start": None,
                        "end": None,
                        "period": None,
                        "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
                        "needs_clarification": True,
                        "clarification_reason": "La consulta no fija claramente instrumento ni rango temporal.",
                    }
                ),
                [],
            )

        with patch("src.graph.nodes.build_llm_data_request", side_effect=_blocked_data_request):
            state = self.workflow.invoke(FinancialQueryInput(query="Analiza el oro"))

        self.assertEqual(state.status, "completed_with_error")
        self.assertIn("instrumento ni rango temporal", state.final_answer)

    def test_operational_repair_can_recover_download(self) -> None:
        # Este test cubre el escenario clave del flujo nuevo:
        # la estructura parece valida, pero la primera descarga falla y el
        # subagente operativo corrige el request para reintentar.
        sample = SAMPLE_INPUTS["overview_aapl"]

        def _fake_data_request(query_input):
            return (
                FinancialDataRequest.from_dict(
                    {
                        "user_query": query_input.query,
                        "provider": "yfinance",
                        "instruments": [{"ticker": "AAPL"}],
                        "interval": "1h",
                        "start": None,
                        "end": None,
                        "period": "2y",
                        "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
                        "needs_clarification": False,
                        "clarification_reason": None,
                    }
                ),
                [],
            )

        def _repair_data_request(query_input, previous_request, validation_errors, stage):
            self.assertEqual(stage, "operational")
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
                ["Se reparo operativamente el FinancialDataRequest."],
            )

        def _fake_analysis(query_input, input_payload=None):
            return (
                AnalysisPlan(
                    analytical_goal="Analisis AAPL",
                    analysis_type="historical_overview",
                    metrics=["rows"],
                    required_columns=["Date", "Close"],
                    data_requirements=["CSV historico normalizado"],
                    output_requirements=["JSON con metricas y resumen"],
                    presentation_preferences=["resumen breve"],
                    reasoning="Analisis simulado para tests.",
                ),
                [],
            )

        def _fake_code(query_input, plan, input_payload=None):
            return (
                """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({"metrics": {"tickers": payload["tickers"]}, "summary": "ok", "limitations": []}, ensure_ascii=False))


if __name__ == "__main__":
    main()
                """.strip(),
                [],
            )

        with (
            patch("src.graph.nodes.build_llm_data_request", side_effect=_fake_data_request),
            patch("src.graph.nodes.repair_llm_data_request", side_effect=_repair_data_request),
            patch("src.graph.nodes.download_market_data", side_effect=[pd.DataFrame(), _mock_yfinance_output(sample["csv_paths"][0])]),
            patch("src.graph.nodes.build_llm_analysis", side_effect=_fake_analysis),
            patch("src.graph.nodes.build_llm_code", side_effect=_fake_code),
            patch(
                "src.graph.nodes.build_llm_code_validation",
                return_value=(
                    CodeValidationDecision(
                        decision="valid",
                        errors=[],
                        warnings=[],
                        required_fixes=[],
                        reasoning="El codigo puede continuar.",
                    ),
                    [],
                ),
            ),
            patch("src.graph.nodes.build_llm_interpretation", return_value=("ok", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(sample))

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.operational_repair_attempts, 1)


if __name__ == "__main__":
    unittest.main()
