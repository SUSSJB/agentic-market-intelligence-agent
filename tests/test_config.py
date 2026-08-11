"""Tests for the Settings loader."""
from __future__ import annotations

import dataclasses

import pytest

from market_intel.config import ConfigError, Settings


VALID_ENV = {
    "MARKET_INTEL_ENV": "test",
    "MARKET_INTEL_LOG_LEVEL": "DEBUG",
    "MARKET_INTEL_DATA_DIR": "/tmp/mi-data",
    "MARKET_INTEL_HTTP_TIMEOUT_SECONDS": "12",
}


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


def test_settings_uses_explicit_source_over_os_environ(monkeypatch):
    for key in VALID_ENV:
        monkeypatch.delenv(key, raising=False)

    settings = Settings.from_env(source=dict(VALID_ENV))

    assert settings.env == "test"
    assert settings.http_timeout_seconds == 12


def test_settings_empty_string_treated_as_missing():
    src = dict(VALID_ENV)
    src["MARKET_INTEL_ENV"] = ""

    with pytest.raises(ConfigError) as exc_info:
        Settings.from_env(source=src)
    assert "MARKET_INTEL_ENV" in str(exc_info.value)


def test_settings_error_message_lists_all_missing_keys():
    with pytest.raises(ConfigError) as exc_info:
        Settings.from_env(source={})

    message = str(exc_info.value)
    for key in VALID_ENV:
        assert key in message


@pytest.mark.parametrize(
    "missing_key",
    [
        "MARKET_INTEL_ENV",
        "MARKET_INTEL_LOG_LEVEL",
        "MARKET_INTEL_DATA_DIR",
        "MARKET_INTEL_HTTP_TIMEOUT_SECONDS",
    ],
)
def test_settings_rejects_each_individual_missing_key(missing_key):
    src = {k: v for k, v in VALID_ENV.items() if k != missing_key}

    with pytest.raises(ConfigError) as exc_info:
        Settings.from_env(source=src)
    assert missing_key in str(exc_info.value)


def test_settings_is_frozen_dataclass():
    settings = Settings.from_env(source=dict(VALID_ENV))

    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.env = "mutated"  # type: ignore[misc]


def test_settings_accepts_negative_and_zero_timeout():
    src = dict(VALID_ENV)
    src["MARKET_INTEL_HTTP_TIMEOUT_SECONDS"] = "0"
    assert Settings.from_env(source=src).http_timeout_seconds == 0

    src["MARKET_INTEL_HTTP_TIMEOUT_SECONDS"] = "-5"
    assert Settings.from_env(source=src).http_timeout_seconds == -5


def test_config_error_is_runtime_error_subclass():
    assert issubclass(ConfigError, RuntimeError)


def test_settings_timeout_error_chains_original_valueerror():
    src = dict(VALID_ENV)
    src["MARKET_INTEL_HTTP_TIMEOUT_SECONDS"] = "abc"

    with pytest.raises(ConfigError) as exc_info:
        Settings.from_env(source=src)
    assert isinstance(exc_info.value.__cause__, ValueError)
