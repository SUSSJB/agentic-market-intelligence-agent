"""Runtime configuration for the market-intelligence agent.

Reads settings from environment variables. The set of required keys mirrors
`.env.example`, which is the source of truth for the environment contract.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised when the runtime environment is missing or malformed."""


@dataclass(frozen=True)
class Settings:
    env: str
    log_level: str
    data_dir: str
    http_timeout_seconds: int

    @classmethod
    def from_env(cls, source: dict[str, str] | None = None) -> "Settings":
        src = source if source is not None else os.environ
        missing = [
            key
            for key in (
                "MARKET_INTEL_ENV",
                "MARKET_INTEL_LOG_LEVEL",
                "MARKET_INTEL_DATA_DIR",
                "MARKET_INTEL_HTTP_TIMEOUT_SECONDS",
            )
            if not src.get(key)
        ]
        if missing:
            raise ConfigError(
                f"missing required environment variables: {', '.join(missing)}"
            )
        try:
            timeout = int(src["MARKET_INTEL_HTTP_TIMEOUT_SECONDS"])
        except ValueError as exc:
            raise ConfigError(
                "MARKET_INTEL_HTTP_TIMEOUT_SECONDS must be an integer"
            ) from exc
        return cls(
            env=src["MARKET_INTEL_ENV"],
            log_level=src["MARKET_INTEL_LOG_LEVEL"],
            data_dir=src["MARKET_INTEL_DATA_DIR"],
            http_timeout_seconds=timeout,
        )
