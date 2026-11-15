"""Unit Tests for Server-Side Credential Isolation and Zero-Leakage (Feature F19)."""

import os
import pytest

from app.core.config import Settings
from app.infrastructure.llm_client import OpenAILLMClient, get_llm_client
from app.infrastructure.mock_engine import MockLLMClient


class TestCredentialIsolation:
    """Verifies that API keys and sensitive credentials never leak into strings, logs, or exceptions."""

    CANARY_KEY = "sk-canary-secret-do-not-leak-9999-alpha"

    def test_settings_repr_masks_api_key(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", self.CANARY_KEY)
        test_settings = Settings()

        assert test_settings.LLM_API_KEY == self.CANARY_KEY
        repr_str = repr(test_settings)
        str_str = str(test_settings)

        assert self.CANARY_KEY not in repr_str, "CRITICAL: Secret API key leaked in repr(settings)"
        assert self.CANARY_KEY not in str_str, "CRITICAL: Secret API key leaked in str(settings)"
        assert "***" in repr_str

    def test_openai_client_repr_masks_api_key(self):
        client = OpenAILLMClient(api_key=self.CANARY_KEY)
        repr_str = repr(client)
        str_str = str(client)

        assert self.CANARY_KEY not in repr_str, "CRITICAL: Secret API key leaked in repr(OpenAILLMClient)"
        assert self.CANARY_KEY not in str_str, "CRITICAL: Secret API key leaked in str(OpenAILLMClient)"
        assert "***" in repr_str

    def test_fallback_to_mock_when_key_is_missing(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "")
        monkeypatch.setenv("USE_MOCK_LLM", "false")
        test_settings = Settings()

        assert test_settings.is_mock_mode is True

    def test_fallback_to_mock_when_use_mock_llm_is_true(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", self.CANARY_KEY)
        monkeypatch.setenv("USE_MOCK_LLM", "true")
        test_settings = Settings()

        assert test_settings.is_mock_mode is True

    def test_fallback_to_mock_when_key_is_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "mock")
        monkeypatch.setenv("USE_MOCK_LLM", "false")
        test_settings = Settings()

        assert test_settings.is_mock_mode is True

    def test_real_mode_engaged_when_valid_key_and_mock_disabled(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", self.CANARY_KEY)
        monkeypatch.setenv("USE_MOCK_LLM", "false")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
        test_settings = Settings()

        assert test_settings.is_mock_mode is False

    def test_zero_secret_leak_in_exceptions(self):
        """Ensure caught exceptions do not echo raw secrets in trace strings."""
        try:
            client = OpenAILLMClient(api_key=self.CANARY_KEY)
            raise ValueError(f"Failed operation with client: {client}")
        except ValueError as e:
            err_msg = str(e)
            assert self.CANARY_KEY not in err_msg
            assert "***" in err_msg
