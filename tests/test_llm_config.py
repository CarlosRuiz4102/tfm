from __future__ import annotations

import unittest
from unittest.mock import patch

from src.config import LLMConfig
from src.llm.client import _repair_mojibake, create_llm_client


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

    def test_llm_config_reads_groq_profile(self) -> None:
        env = {
            "LLM_PROFILE": "groq",
            "GROQ_API_KEY": "test-groq-key",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "groq")
        self.assertEqual(config.base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(config.api_key, "test-groq-key")
        self.assertEqual(config.model, "llama-3.3-70b-versatile")

    def test_llm_config_reads_gemini_profile(self) -> None:
        env = {
            "LLM_PROFILE": "gemini",
            "GEMINI_API_KEY": "test-gemini-key",
            "GEMINI_MODEL": "gemini-test-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "gemini")
        self.assertEqual(config.base_url, "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.assertEqual(config.api_key, "test-gemini-key")
        self.assertEqual(config.model, "gemini-test-model")

    def test_llm_config_reads_university_profile(self) -> None:
        env = {
            "LLM_PROFILE": "university",
            "UNIVERSITY_BASE_URL": "https://university.example/openai/v1",
            "UNIVERSITY_API_KEY": "test-university-key",
            "UNIVERSITY_MODEL": "university-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "university")
        self.assertEqual(config.base_url, "https://university.example/openai/v1")
        self.assertEqual(config.api_key, "test-university-key")
        self.assertEqual(config.model, "university-model")

    def test_repairs_mojibake_from_llm_response(self) -> None:
        text = "El precio pasÃ³ de 13.34â€¯USD. AnÃ¡lisis tÃ©cnico."

        repaired = _repair_mojibake(text)

        self.assertEqual(repaired, "El precio pasó de 13.34 USD. Análisis técnico.")


if __name__ == "__main__":
    unittest.main()
