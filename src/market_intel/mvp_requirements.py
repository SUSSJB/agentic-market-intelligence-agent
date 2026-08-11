"""MVP Requirements: canonical contract for the market-intelligence agent's MVP.

This module defines the *shape* of the MVP contract (requirements, input and
output contracts, and a validator for candidate forecast payloads).

Public surface:
    * :class:`Requirement` — a single MVP requirement (frozen dataclass).
    * :class:`MVPSpec` — the canonical, immutable spec (frozen dataclass).
    * :class:`RequirementsError` — raised when a payload violates the contract.
    * :func:`load_mvp_spec` — returns the deterministic MVP spec.
    * :func:`validate_forecast_shape` — validates a candidate forecast payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"input", "output", "behaviour", "operability"}
)


class RequirementsError(ValueError):
    """Raised when an MVP spec or candidate payload violates the contract."""


@dataclass(frozen=True)
class Requirement:
    """A single MVP requirement.

    Attributes:
        id: Stable identifier (e.g. ``"MVP-R1"``).
        title: Short human-readable title.
        description: One-sentence description of the requirement.
        category: One of ``{"input", "output", "behaviour", "operability"}``.
    """

    id: str
    title: str
    description: str
    category: str


@dataclass(frozen=True)
class MVPSpec:
    """The canonical MVP contract for the market-intelligence agent.

    Attributes:
        required_inputs: Tuple of field names the MVP must accept as input for
            each market observation (e.g. ``"symbol"``, ``"timestamp"``,
            ``"open"``, ``"close"``, ``"volume"``).
        required_outputs: Tuple of field names present on every forecast the
            MVP emits (e.g. ``"symbol"``, ``"predicted_open"``,
            ``"forecast_for"``, ``"confidence"``, ``"generated_at"``).
        requirements: Ordered tuple of :class:`Requirement` entries.
    """

    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    requirements: tuple[Requirement, ...]


_REQUIRED_INPUTS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "open",
    "close",
    "volume",
)

_REQUIRED_OUTPUTS: tuple[str, ...] = (
    "symbol",
    "predicted_open",
    "forecast_for",
    "confidence",
    "generated_at",
)

_REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        id="MVP-R1",
        title="Accept OHLCV observations",
        description=(
            "The agent must accept market observations carrying symbol, "
            "timestamp, open, close, and volume fields."
        ),
        category="input",
    ),
    Requirement(
        id="MVP-R2",
        title="Emit next-open forecast payload",
        description=(
            "Every forecast must include the target symbol, predicted open, "
            "the session it forecasts, a confidence score, and a generation "
            "timestamp."
        ),
        category="output",
    ),
    Requirement(
        id="MVP-R3",
        title="Deliver detailed market movement insights",
        description=(
            "Forecasts must summarise the drivers behind predicted moves so "
            "financial analysts can act on them for investment decisions."
        ),
        category="behaviour",
    ),
    Requirement(
        id="MVP-R4",
        title="Deterministic, auditable runs",
        description=(
            "Given the same inputs and configuration, the agent must produce "
            "the same forecast so runs are reproducible and auditable."
        ),
        category="operability",
    ),
)


def load_mvp_spec() -> MVPSpec:
    """Return the canonical, immutable MVP spec for the agent.

    Deterministic: repeated calls return equal :class:`MVPSpec` instances.
    """
    return MVPSpec(
        required_inputs=_REQUIRED_INPUTS,
        required_outputs=_REQUIRED_OUTPUTS,
        requirements=_REQUIREMENTS,
    )


def validate_forecast_shape(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` conforms to :attr:`MVPSpec.required_outputs`.

    Raises:
        RequirementsError: If ``payload`` is not a dict, is missing any
            required output field, or has empty values (``None`` or empty
            string) for required fields.
    """
    if not isinstance(payload, dict):
        raise RequirementsError(
            f"forecast payload must be a dict, got {type(payload).__name__}"
        )

    spec = load_mvp_spec()
    missing = [field for field in spec.required_outputs if field not in payload]
    if missing:
        raise RequirementsError(
            f"forecast payload missing required field(s): {', '.join(missing)}"
        )

    empty = [
        field
        for field in spec.required_outputs
        if payload[field] is None
        or (isinstance(payload[field], str) and payload[field] == "")
    ]
    if empty:
        raise RequirementsError(
            f"forecast payload has empty value(s) for required field(s): "
            f"{', '.join(empty)}"
        )


__all__ = [
    "MVPSpec",
    "Requirement",
    "RequirementsError",
    "load_mvp_spec",
    "validate_forecast_shape",
]
