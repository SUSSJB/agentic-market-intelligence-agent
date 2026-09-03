"""Market-Intensity Agent: canonical market-intensity analysis contract.

Defines the shape of the Market-Intensity Agent contract for the
market-intelligence agent -- covering volume, volatility, momentum, and
sentiment intensity signals derived from market data.

Public surface:
    * :class:`MarketSignal` -- a single market-intensity signal (frozen dataclass).
    * :class:`MarketIntensitySpec` -- the canonical, immutable market-intensity
      spec (frozen dataclass).
    * :class:`MarketIntensityError` -- raised when an intensity analysis payload
      violates the contract.
    * :func:`load_market_intensity_spec` -- returns the deterministic
      market-intensity spec.
    * :func:`analyze_market_intensity` -- validates a candidate intensity
      analysis payload.
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


_SIGNALS: tuple[MarketSignal, ...] = (
    MarketSignal(
        id="MIA-R1",
        title="Trading Volume Surge",
        description=(
            "Measures abnormal trading volume activity relative to the historical average,"
            " indicating heightened market participation or liquidity events."
        ),
        category="volume",
    ),
    MarketSignal(
        id="MIA-R2",
        title="Price Volatility Range",
        description=(
            "Tracks intraday price swing and fluctuation width to quantify short-term volatility"
            " and detect potential breakout or breakdown conditions."
        ),
        category="volatility",
    ),
    MarketSignal(
        id="MIA-R3",
        title="Trend Momentum Rate",
        description=(
            "Evaluates the speed and direction of price trend progression using rate-of-change"
            " indicators to identify strengthening or weakening momentum."
        ),
        category="momentum",
    ),
    MarketSignal(
        id="MIA-R4",
        title="Market Sentiment Mood",
        description=(
            "Aggregates bullish and bearish signals from options flow, news tone, and social"
            " sentiment to gauge overall market mood and investor fear/greed balance."
        ),
        category="sentiment",
    ),
    MarketSignal(
        id="MIA-R5",
        title="Crypto Overnight Futures Volume",
        description=(
            "Tracks BTC and ETH overnight futures contract volume and open interest to detect"
            " institutional flow and overnight liquidity shifts in crypto markets."
        ),
        category="volume",
    ),
    MarketSignal(
        id="MIA-R6",
        title="Crypto Overnight Futures Funding Rate",
        description=(
            "Monitors perpetual futures funding rates and basis spread for BTC and ETH to"
            " quantify overnight volatility pressure and leverage imbalance in crypto."
        ),
        category="volatility",
    ),
)

_SPEC = MarketIntensitySpec(
    required_analysis_fields=_REQUIRED_ANALYSIS_FIELDS,
    signals=_SIGNALS,
)


def load_market_intensity_spec() -> MarketIntensitySpec:
    """Return the canonical, immutable market-intensity spec.

    Deterministic: repeated calls return equal :class:`MarketIntensitySpec` instances.
    """
    return _SPEC


def analyze_market_intensity(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` meets the market-intensity analysis contract.

    Empty values are defined as ``None`` or the empty string ``""``.
    Whitespace-only strings, ``0``, and ``False`` are accepted.

    Raises:
        MarketIntensityError: If ``payload`` is not a dict, is missing any
            required analysis field, or has empty values (``None`` or empty
            string) for required fields.
    """
    if not isinstance(payload, dict):
        raise MarketIntensityError(
            f"payload must be a dict, got {type(payload).__name__}"
        )

    errors: list[str] = []

    missing = [f for f in _REQUIRED_ANALYSIS_FIELDS if f not in payload]
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    empty = [
        f
        for f in _REQUIRED_ANALYSIS_FIELDS
        if f in payload and (payload[f] is None or payload[f] == "")
    ]
    if empty:
        errors.append(f"empty required fields: {', '.join(empty)}")

    if errors:
        raise MarketIntensityError("; ".join(errors))


__all__ = [
    "MarketIntensityError",
    "MarketIntensitySpec",
    "MarketSignal",
    "analyze_market_intensity",
    "load_market_intensity_spec",
]
