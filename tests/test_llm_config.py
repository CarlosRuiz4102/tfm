from __future__ import annotations

import unittest
from unittest.mock import patch

from src.config import LLMConfig
from src.llm.client import create_llm_client


class LLMConfigTests(unittest.TestCase):
    def test_llm_is_disabled_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            config = LLMConfig.from_env()

        self.assertFalse(config.enabled)
        self.assertFalse(config.is_configured)

    def test_llm_config_reads_generic_environment(self) -> None:
        env = {
            "LLM_ENABLED": "true",
            "LLM_BASE_URL": "https://example.test/v1",
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "test-model",
            "LLM_USE_FOR_INTERPRETATION": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.enabled)
        self.assertTrue(config.is_configured)
        self.assertEqual(config.base_url, "https://example.test/v1")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "test-model")
        self.assertTrue(config.use_for_interpretation)
        self.assertFalse(config.use_for_codegen)

    def test_create_client_returns_none_when_disabled(self) -> None:
        config = LLMConfig(
            enabled=False,
            provider="openai-compatible",
            profile="",
            base_url=None,
            api_key="",
            model="",
            temperature=0.1,
            max_tokens=128,
            timeout_seconds=10,
            use_for_planning=False,
            use_for_codegen=False,
            use_for_interpretation=False,
        )

        self.assertIsNone(create_llm_client(config))

    def test_llm_config_reads_groq_profile(self) -> None:
        env = {
            "LLM_ENABLED": "true",
            "LLM_PROFILE": "groq",
            "GROQ_API_KEY": "test-groq-key",
            "LLM_USE_FOR_INTERPRETATION": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.enabled)
        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "groq")
        self.assertEqual(config.base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(config.api_key, "test-groq-key")
        self.assertEqual(config.model, "llama-3.3-70b-versatile")

    def test_llm_config_reads_gemini_profile(self) -> None:
        env = {
            "LLM_ENABLED": "true",
            "LLM_PROFILE": "gemini",
            "GEMINI_API_KEY": "test-gemini-key",
            "GEMINI_MODEL": "gemini-test-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.enabled)
        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "gemini")
        self.assertEqual(config.base_url, "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.assertEqual(config.api_key, "test-gemini-key")
        self.assertEqual(config.model, "gemini-test-model")

    def test_llm_config_reads_university_profile(self) -> None:
        env = {
            "LLM_ENABLED": "true",
            "LLM_PROFILE": "university",
            "UNIVERSITY_BASE_URL": "https://university.example/openai/v1",
            "UNIVERSITY_API_KEY": "test-university-key",
            "UNIVERSITY_MODEL": "university-model",
        }
        with patch.dict("os.environ", env, clear=True):
            config = LLMConfig.from_env()

        self.assertTrue(config.enabled)
        self.assertTrue(config.is_configured)
        self.assertEqual(config.profile, "university")
        self.assertEqual(config.base_url, "https://university.example/openai/v1")
        self.assertEqual(config.api_key, "test-university-key")
        self.assertEqual(config.model, "university-model")


if __name__ == "__main__":
    unittest.main()
