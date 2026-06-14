from __future__ import annotations

import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import pandas as pd

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import AnalysisPlan, CodeValidationDecision, FinancialDataRequest, FinancialQueryInput


def _mock_yfinance_output(csv_path: str) -> pd.DataFrame:
    # Reutilizamos CSVs congelados para que la traza se pruebe sin red.
    dataframe = pd.read_csv(Path(csv_path), header=[0, 1], index_col=0)
    dataframe.index = pd.to_datetime(dataframe.index)
    dataframe.index.name = "Date"
    return dataframe


class WorkflowTracingTests(unittest.TestCase):
    """Comprueba que una ejecucion deje una traza legible y completa."""

    def setUp(self) -> None:
        self.workflow = build_workflow()
        self.sample = SAMPLE_INPUTS["overview_aapl"]
        self.created_trace_dirs: list[Path] = []

    def tearDown(self) -> None:
        for trace_dir in self.created_trace_dirs:
            if trace_dir.exists():
                shutil.rmtree(trace_dir)

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

    def test_workflow_creates_trace_manifest_events_and_snapshots(self) -> None:
        script = """
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = {
        "metrics": {"tickers": payload["tickers"], "csv_count": len(payload["csv_paths"])},
        "summary": "AAPL se proceso correctamente.",
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
            patch("src.graph.nodes.build_llm_code", return_value=(script, [])),
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
            patch("src.graph.nodes.build_llm_interpretation", return_value=("Respuesta final AAPL.", [])),
        ):
            state = self.workflow.invoke(FinancialQueryInput.from_dict(self.sample))

        self.assertEqual(state.status, "completed")
        self.assertTrue(state.run_id)
        self.assertIsNotNone(state.trace_dir)

        trace_dir = Path(state.trace_dir)
        self.created_trace_dirs.append(trace_dir)

        manifest_path = trace_dir / "manifest.json"
        events_path = trace_dir / "events.jsonl"
        snapshots_dir = trace_dir / "snapshots"

        self.assertTrue(manifest_path.exists())
        self.assertTrue(events_path.exists())
        self.assertTrue(snapshots_dir.exists())
        self.assertTrue((snapshots_dir / "00_initial_state.json").exists())
        self.assertTrue((snapshots_dir / "09_interpretation_node.json").exists())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["run_id"], state.run_id)
        self.assertEqual(manifest["current_status"], "completed")
        self.assertEqual(manifest["query"], self.sample["query"])
        self.assertIn("interpretation_node", manifest["node_order"])

        events_lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(events_lines), 3)
        self.assertIn('"event_type": "workflow_started"', events_lines[0])
        self.assertIn('"event_type": "workflow_finished"', events_lines[-1])

        # La traza operativa no debe reintroducir pistas resumidas sobre
        # analysis_plan en los eventos compactos de depuracion.
        self.assertNotIn("has_analysis_plan", events_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
