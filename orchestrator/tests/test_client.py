import pytest

from orchestrator.client import API_KEY_ENV_VAR, LLMClient, MissingAPIKeyError


def test_raises_when_no_key_anywhere(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    with pytest.raises(MissingAPIKeyError):
        LLMClient(model="claude-sonnet-5")


def test_picks_up_key_from_env(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-test-from-env")
    client = LLMClient(model="claude-sonnet-5")
    assert client._client.api_key == "sk-test-from-env"


def test_explicit_api_key_overrides_env(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-test-from-env")
    client = LLMClient(model="claude-sonnet-5", api_key="sk-test-explicit")
    assert client._client.api_key == "sk-test-explicit"


def test_explicit_api_key_works_without_env(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    client = LLMClient(model="claude-sonnet-5", api_key="sk-test-explicit")
    assert client._client.api_key == "sk-test-explicit"
