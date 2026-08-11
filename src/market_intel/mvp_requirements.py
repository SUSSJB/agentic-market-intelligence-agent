"""MVP Requirements: contract stubs for the market-intelligence agent's MVP.

This module defines the *shape* of the MVP contract (requirements, input and
output contracts, and a validator for candidate forecast payloads). It is
introduced as part of the TDD scaffolding ticket (PRODMARKET-3): the tests
in ``tests/test_mvp_requirements.py`` describe the intended behaviour, and
every callable here raises :class:`NotImplementedError` so that the tests
fail deterministically until the implementation ticket lands.

No production behaviour lives in this file yet — only names, types, and
docstrings that lock the contract for the next ticket.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


def load_mvp_spec() -> MVPSpec:
    """Return the canonical, immutable MVP spec for the agent.

    Must be deterministic — repeated calls return equal specs.
    """
    raise NotImplementedError("load_mvp_spec is defined by PRODMARKET-3 tests only")


def validate_forecast_shape(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` conforms to :attr:`MVPSpec.required_outputs`.

    Raises:
        RequirementsError: If ``payload`` is not a dict, is missing any
            required output field, or has empty values for required fields.
    """
    raise NotImplementedError(
        "validate_forecast_shape is defined by PRODMARKET-3 tests only"
    )


__all__ = [
    "MVPSpec",
    "Requirement",
    "RequirementsError",
    "load_mvp_spec",
    "validate_forecast_shape",
]
