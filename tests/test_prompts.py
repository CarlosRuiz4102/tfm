from __future__ import annotations

import unittest

from src.llm.prompts import (
    build_analysis_messages,
    build_code_repair_messages,
    build_code_validation_messages,
)
from src.llm.pipeline import _code_from_text
from src.schemas import AnalysisPlan, FinancialQueryInput


class PromptContractsTests(unittest.TestCase):
    """Protege instrucciones clave del workflow para evitar regresiones sutiles."""

    def setUp(self) -> None:
        self.query_input = FinancialQueryInput(query="Compara QQQ y SPY en 2024.")
        self.plan = AnalysisPlan(
            analytical_goal="Comparar rentabilidad y volatilidad.",
            analysis_type="comparative_return_analysis",
            metrics=["cumulative_return", "daily_volatility"],
            required_columns=["Date", "Ticker", "Adj Close"],
            data_requirements=["Usar CSV historico normalizado."],
            output_requirements=["JSON con metrics, summary y limitations."],
            presentation_preferences=["Resumen breve y claro."],
            reasoning="Plan de prueba.",
        )

    def test_analysis_prompt_requires_non_empty_output_and_presentation_requirements(self) -> None:
        messages = build_analysis_messages(self.query_input)
        user_message = messages[-1].content
        self.assertIn("output_requirements y presentation_preferences no pueden quedar vacios", user_message)
        self.assertIn("metrics debe ser un objeto JSON, summary debe ser un texto plano y limitations debe ser una lista", user_message)

    def test_code_validation_prompt_distinguishes_validator_schema_from_script_output(self) -> None:
        messages = build_code_validation_messages(self.query_input, self.plan, "print('ok')")
        user_message = messages[-1].content
        self.assertIn("No confundas el esquema JSON de tu propia respuesta", user_message)
        self.assertIn('"required_top_level_keys": ["metrics", "summary", "limitations"]', user_message)
        self.assertIn("Considera validos, por contrato del workflow, los helpers importados desde src.execution.market_data", user_message)

    def test_code_repair_prompt_preserves_workflow_output_contract(self) -> None:
        messages = build_code_repair_messages(self.query_input, self.plan, "print('ok')", "error")
        user_message = messages[-1].content
        self.assertIn("No cambies el contrato de entrada ni el contrato de salida del workflow", user_message)
        self.assertIn("metrics, summary y limitations", user_message)
        self.assertIn("metrics sea un objeto, summary sea un texto y limitations sea una lista", user_message)

    def test_code_extraction_unwraps_nested_code_json(self) -> None:
        wrapped = '{"code":"{\\"code\\":\\"import json\\\\nprint(1)\\"}"}'
        self.assertEqual(_code_from_text(wrapped), "import json\nprint(1)")


if __name__ == "__main__":
    unittest.main()
