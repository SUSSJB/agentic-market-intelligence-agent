"""Acceptance Test Plan: canonical contract for the market-intelligence agent.

This module defines the *shape* of the Acceptance Test Plan (ATP) that pins
what "done" means for the next-open forecast MVP. It is deliberately a
contract-only module in this ticket (PRODMARKET-5): the concrete plan is
scaffolded here but the factories raise :class:`NotImplementedError` until
the implementation ticket lands.

Public surface:
    * :class:`AcceptanceCase` -- a single acceptance test case (frozen dataclass).
    * :class:`AcceptanceTestPlan` -- the canonical, immutable plan (frozen dataclass).
    * :class:`TestPlanError` -- raised when a plan or a test-result payload
      violates the contract.
    * :func:`load_acceptance_test_plan` -- returns the deterministic ATP.
    * :func:`validate_test_result` -- validates a candidate test-result payload.

TDD note
--------
The ``load_acceptance_test_plan`` and ``validate_test_result`` factories
raise :class:`NotImplementedError` in this ticket so the behaviour tests
introduced under PRODMARKET-5 can be pinned as ``xfail(strict=True,
raises=NotImplementedError)`` and flip to XPASS the moment the follow-up
implementation ticket makes them pass. See ``ARCHITECTURE.md`` for the TDD
convention this repository follows.
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
    """A single acceptance test case.

    Attributes:
        id: Stable identifier (e.g. ``"ATP-C1"``).
        title: Short human-readable title.
        given: Precondition ("given ...") description.
        when: Trigger ("when ...") description.
        then: Expected outcome ("then ...") description.
        category: One of ``{"happy_path", "edge_case", "regression"}``.
        covers: Tuple of MVP requirement ids this case exercises
            (e.g. ``("MVP-R1", "MVP-R2")``).
    """

    id: str
    title: str
    given: str
    when: str
    then: str
    category: str
    covers: tuple[str, ...]


@dataclass(frozen=True)
class AcceptanceTestPlan:
    """The canonical Acceptance Test Plan for the market-intelligence agent.

    Attributes:
        cases: Ordered tuple of :class:`AcceptanceCase` entries.
        required_result_fields: Tuple of field names present on every
            test-result payload the ATP accepts
            (e.g. ``"case_id"``, ``"status"``, ``"executed_at"``, ``"evidence"``).
    """

    cases: tuple[AcceptanceCase, ...]
    required_result_fields: tuple[str, ...]


def load_acceptance_test_plan() -> AcceptanceTestPlan:
    """Return the canonical, immutable Acceptance Test Plan for the agent.

    Deterministic: repeated calls must return equal :class:`AcceptanceTestPlan`
    instances.

    Raises:
        NotImplementedError: Contract stub -- implementation lands in the
            follow-up DEV ticket for the Acceptance Test Plan component.
    """
    raise NotImplementedError(
        "load_acceptance_test_plan is pending the Acceptance Test Plan "
        "implementation ticket."
    )


def validate_test_result(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` conforms to the ATP result contract.

    Raises:
        TestPlanError: If ``payload`` is not a dict, is missing any
            required field, has empty required values, references an unknown
            ``case_id``, or uses a ``status`` outside the allowed set.
        NotImplementedError: Contract stub -- implementation lands in the
            follow-up DEV ticket for the Acceptance Test Plan component.
    """
    raise NotImplementedError(
        "validate_test_result is pending the Acceptance Test Plan "
        "implementation ticket."
    )


__all__ = [
    "AcceptanceCase",
    "AcceptanceTestPlan",
    "TestPlanError",
    "load_acceptance_test_plan",
    "validate_test_result",
]
