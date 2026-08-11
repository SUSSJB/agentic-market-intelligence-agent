"""Tests for the Settings loader."""
from __future__ import annotations

import pytest

from market_intel.config import ConfigError, Settings


def test_settings_from_env_reads_all_required_keys(monkeypatch):
    monkeypatch.setenv("MARKET_INTEL_ENV", "test")
    monkeypatch.setenv("MARKET_INTEL_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", "/tmp/mi-data")
    monkeypatch.setenv("MARKET_INTEL_HTTP_TIMEOUT_SECONDS", "12")

    settings = Settings.from_env()

    assert settings.env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.data_dir == "/tmp/mi-data"
    assert settings.http_timeout_seconds == 12


def test_settings_from_env_raises_when_required_key_missing(monkeypatch):
    for key in (
        "MARKET_INTEL_ENV",
        "MARKET_INTEL_LOG_LEVEL",
        "MARKET_INTEL_DATA_DIR",
        "MARKET_INTEL_HTTP_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ConfigError) as exc_info:
        Settings.from_env()
    assert "MARKET_INTEL_ENV" in str(exc_info.value)


def test_settings_rejects_non_integer_timeout(monkeypatch):
    monkeypatch.setenv("MARKET_INTEL_ENV", "test")
    monkeypatch.setenv("MARKET_INTEL_LOG_LEVEL", "INFO")
    monkeypatch.setenv("MARKET_INTEL_DATA_DIR", "/tmp/mi-data")
    monkeypatch.setenv("MARKET_INTEL_HTTP_TIMEOUT_SECONDS", "not-a-number")

    with pytest.raises(ConfigError):
        Settings.from_env()
