"""Market-Intensity Agent: canonical market-intensity analysis contract.

Defines the shape of the Market-Intensity Agent contract for the
market-intelligence agent — covering volume, volatility, momentum, and
sentiment intensity signals derived from market data.

Public surface:
    * :class:`MarketSignal` — a single market-intensity signal (frozen dataclass).
    * :class:`MarketIntensitySpec` — the canonical, immutable market-intensity spec (frozen dataclass).
    * :class:`MarketIntensityError` — raised when an intensity analysis payload violates the contract.
    * :func:`load_market_intensity_spec` — returns the deterministic market-intensity spec.
    * :func:`analyze_market_intensity` — validates a candidate intensity analysis payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"volume", "volatility", "momentum", "sentiment"}
)

_REQUIRED_ANALYSIS_FIELDS: tuple[str, ...] = (
    "signal_id",
    "symbol",
    "intensity_score",
    "intensity_level",
    "timestamp",
)


class MarketIntensityError(ValueError):
    """Raised when a market-intensity spec or analysis payload violates the contract."""


@dataclass(frozen=True)
class MarketSignal:
    """A single market-intensity signal.

    Attributes:
        id: Stable identifier (e.g. ``"MIA-R1"``).
        title: Short human-readable title.
        description: One-sentence description of the signal.
        category: One of ``{"volume", "volatility", "momentum", "sentiment"}``.
    """

    id: str
    title: str
    description: str
    category: str


@dataclass(frozen=True)
class MarketIntensitySpec:
    """The canonical market-intensity analysis contract.

    Attributes:
        required_analysis_fields: Tuple of field names an intensity analysis payload must carry
            (e.g. ``"signal_id"``, ``"symbol"``, ``"intensity_score"``,
            ``"intensity_level"``, ``"timestamp"``).
        signals: Ordered tuple of :class:`MarketSignal` entries.
    """

    required_analysis_fields: tuple[str, ...]
    signals: tuple[MarketSignal, ...]


def load_market_intensity_spec() -> MarketIntensitySpec:
    """Return the canonical, immutable market-intensity spec.

    Deterministic: repeated calls return equal :class:`MarketIntensitySpec` instances.

    Raises:
        NotImplementedError: Until the implementation ticket lands.
    """
    raise NotImplementedError(
        "load_market_intensity_spec is not yet implemented — pending PRODMARKET-12"
    )


def analyze_market_intensity(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` meets the market-intensity analysis contract.

    Empty values are defined as ``None`` or the empty string ``""``.
    Whitespace-only strings, ``0``, and ``False`` are accepted.

    Raises:
        MarketIntensityError: If ``payload`` is not a dict, is missing any
            required analysis field, has empty values (``None`` or empty
            string) for required fields, or carries an unknown ``intensity_level``.
        NotImplementedError: Until the implementation ticket lands.
    """
    raise NotImplementedError(
        "analyze_market_intensity is not yet implemented — pending PRODMARKET-12"
    )


__all__ = [
    "MarketIntensityError",
    "MarketIntensitySpec",
    "MarketSignal",
    "analyze_market_intensity",
    "load_market_intensity_spec",
]
