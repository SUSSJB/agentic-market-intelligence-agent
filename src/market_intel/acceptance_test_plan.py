"""Acceptance Test Plan: canonical contract for the market-intelligence agent.

Public surface:
    * :class:`AcceptanceCase` -- a single acceptance test case (frozen dataclass).
    * :class:`AcceptanceTestPlan` -- the canonical, immutable plan (frozen dataclass).
    * :class:`TestPlanError` -- raised when a plan or a test-result payload
      violates the contract.
    * :func:`load_acceptance_test_plan` -- returns the deterministic ATP.
    * :func:`validate_test_result` -- validates a candidate test-result payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"happy_path", "edge_case", "regression"}
)

_ALLOWED_STATUSES: frozenset[str] = frozenset({"passed", "failed", "skipped"})


class TestPlanError(ValueError):
    """Raised when an ATP or a candidate test-result payload violates the contract."""

    __test__ = False  # keep pytest from trying to collect this as a test class


@dataclass(frozen=True)
class AcceptanceCase:
    """A single acceptance test case."""

    id: str
    title: str
    given: str
    when: str
    then: str
    category: str
    covers: tuple[str, ...]


@dataclass(frozen=True)
class AcceptanceTestPlan:
    """The canonical Acceptance Test Plan for the market-intelligence agent."""

    cases: tuple[AcceptanceCase, ...]
    required_result_fields: tuple[str, ...]


_CASES: tuple[AcceptanceCase, ...] = (
    AcceptanceCase(
        id="ATP-C1",
        title="Valid OHLCV observation is accepted by the agent",
        given="A financial analyst submits a well-formed OHLCV market observation",
        when="The agent processes the observation",
        then="The observation is accepted without error and triggers forecast generation",
        category="happy_path",
        covers=("MVP-R1",),
    ),
    AcceptanceCase(
        id="ATP-C2",
        title="Forecast output contains all required fields",
        given="A valid OHLCV observation has been processed",
        when="The agent emits a next-open forecast",
        then=(
            "The forecast payload includes symbol, predicted_open, forecast_for, "
            "confidence, and generated_at fields with non-empty values"
        ),
        category="happy_path",
        covers=("MVP-R2",),
    ),
    AcceptanceCase(
        id="ATP-C3",
        title="Forecast includes detailed market movement insights for investment decisions",
        given="A financial analyst requests a next-open forecast",
        when="The agent generates the forecast",
        then=(
            "The forecast summarises the key drivers behind predicted price movements "
            "so the analyst can make informed investment decisions"
        ),
        category="happy_path",
        covers=("MVP-R3",),
    ),
    AcceptanceCase(
        id="ATP-C4",
        title="Identical inputs produce identical forecasts",
        given="The same OHLCV observations and configuration are submitted twice",
        when="The agent runs both times",
        then="Both forecast payloads are equal, confirming deterministic output",
        category="happy_path",
        covers=("MVP-R4",),
    ),
    AcceptanceCase(
        id="ATP-C5",
        title="Incomplete OHLCV observation is rejected",
        given="A market observation is submitted with one or more required fields missing",
        when="The agent attempts to validate the observation",
        then=(
            "The agent raises a validation error naming every missing field, "
            "and no forecast is generated"
        ),
        category="edge_case",
        covers=("MVP-R1",),
    ),
    AcceptanceCase(
        id="ATP-C6",
        title="Forecast payload missing required output field is flagged",
        given="An internally generated forecast payload omits a required output field",
        when="The forecast shape validator is called",
        then=(
            "A RequirementsError is raised, naming the missing field, "
            "and the payload is not forwarded to the caller"
        ),
        category="edge_case",
        covers=("MVP-R2",),
    ),
    AcceptanceCase(
        id="ATP-C7",
        title="Forecast output remains stable across agent restarts",
        given="The agent is restarted with the same configuration and historical data",
        when="The same OHLCV observation is submitted after restart",
        then="The forecast matches the pre-restart output, confirming auditability",
        category="regression",
        covers=("MVP-R4",),
    ),
)

_REQUIRED_RESULT_FIELDS: tuple[str, ...] = (
    "case_id",
    "status",
    "executed_at",
    "evidence",
)

_PLAN: AcceptanceTestPlan = AcceptanceTestPlan(
    cases=_CASES,
    required_result_fields=_REQUIRED_RESULT_FIELDS,
)


def load_acceptance_test_plan() -> AcceptanceTestPlan:
    """Return the canonical, immutable Acceptance Test Plan for the agent.

    Deterministic: repeated calls must return equal :class:`AcceptanceTestPlan`
    instances.
    """
    return _PLAN


def validate_test_result(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` conforms to the ATP result contract.

    Raises:
        TestPlanError: If ``payload`` is not a dict, is missing any
            required field, has empty required values, references an unknown
            ``case_id``, or uses a ``status`` outside the allowed set.
    """
    if not isinstance(payload, dict):
        raise TestPlanError(
            f"test-result payload must be a dict, got {type(payload).__name__}"
        )

    plan = load_acceptance_test_plan()

    missing = [f for f in plan.required_result_fields if f not in payload]
    if missing:
        raise TestPlanError(
            f"test-result payload missing required field(s): {', '.join(missing)}"
        )

    empty = [
        f
        for f in plan.required_result_fields
        if payload[f] is None or (isinstance(payload[f], str) and payload[f] == "")
    ]
    if empty:
        raise TestPlanError(
            f"test-result payload has empty value(s) for required field(s): "
            f"{', '.join(empty)}"
        )

    known_ids = {c.id for c in plan.cases}
    case_id = payload.get("case_id")
    if case_id not in known_ids:
        raise TestPlanError(
            f"test-result references unknown case_id: {case_id!r}"
        )

    status = payload.get("status")
    if status not in _ALLOWED_STATUSES:
        raise TestPlanError(
            f"test-result status {status!r} is not allowed; "
            f"must be one of {sorted(_ALLOWED_STATUSES)}"
        )


__all__ = [
    "AcceptanceCase",
    "AcceptanceTestPlan",
    "TestPlanError",
    "load_acceptance_test_plan",
    "validate_test_result",
]
