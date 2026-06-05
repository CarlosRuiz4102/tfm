from __future__ import annotations

import unittest
from unittest.mock import patch

from src.config import LLMConfig
from src.llm.client import _repair_mojibake, create_llm_client
from src.llm.pipeline import _is_json_only_answer


class LLMConfigTests(unittest.TestCase):
    def test_llm_requires_credentials_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            config = LLMConfig.from_env()

        self.assertFalse(config.is_configured)

    def test_llm_config_reads_generic_environment(self) -> None:
        env = {
            "LLM_BASE_URL": "https://example.test/v1",
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "test-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.base_url, "https://example.test/v1")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "test-model")

    def test_create_client_returns_none_when_unconfigured(self) -> None:
        config = LLMConfig(
            provider="openai-compatible",
            profile="",
            base_url=None,
            api_key="",
            model="",
            temperature=0.1,
            max_tokens=128,
            timeout_seconds=10,
            verify_ssl=True,
        )

        self.assertIsNone(create_llm_client(config))

    def test_llm_config_reads_openai_environment(self) -> None:
        env = {
            "OPENAI_API_KEY": "test-openai-key",
            "OPENAI_MODEL": "gpt-test-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "openai")
        self.assertIsNone(config.base_url)
        self.assertEqual(config.api_key, "test-openai-key")
        self.assertEqual(config.model, "gpt-test-model")

    def test_llm_config_uses_default_openai_model(self) -> None:
        env = {
            "OPENAI_API_KEY": "test-openai-key",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "openai")
        self.assertEqual(config.api_key, "test-openai-key")
        self.assertEqual(config.model, "openai/gpt-oss-20b")

    def test_llm_config_reads_vllm_environment(self) -> None:
        env = {
            "VLLM_BASE_URL": "https://vllm.example.test/v1",
            "VLLM_API_KEY": "test-vllm-key",
            "VLLM_MODEL": "openai/gpt-oss-20b",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "openai")
        self.assertEqual(config.base_url, "https://vllm.example.test/v1")
        self.assertEqual(config.api_key, "test-vllm-key")
        self.assertEqual(config.model, "openai/gpt-oss-20b")

    def test_llm_config_reads_university_vllm_aliases(self) -> None:
        env = {
            "UNIVERSITY_BASE_URL": "https://university-vllm.example.test/v1",
            "UNIVERSITY_API_KEY": "test-university-key",
            "UNIVERSITY_MODEL": "openai/gpt-oss-20b",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "openai")
        self.assertEqual(config.base_url, "https://university-vllm.example.test/v1")
        self.assertEqual(config.api_key, "test-university-key")
        self.assertEqual(config.model, "openai/gpt-oss-20b")

    def test_repairs_mojibake_from_llm_response(self) -> None:
        text = "El precio pasÃ³ de 13.34â€¯USD. AnÃ¡lisis tÃ©cnico."

        repaired = _repair_mojibake(text)

        self.assertEqual(repaired, "El precio pasó de 13.34 USD. Análisis técnico.")

    def test_detects_json_only_interpretation_answer(self) -> None:
        self.assertTrue(_is_json_only_answer('{"retorno_total": 12.7, "cagr": 0.68}'))
        self.assertFalse(_is_json_only_answer("Nvidia crecio un 1273.33% segun los datos historicos."))


if __name__ == "__main__":
    unittest.main()
