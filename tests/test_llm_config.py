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


if __name__ == "__main__":
    unittest.main()
