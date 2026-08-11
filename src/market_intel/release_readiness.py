"""Release Readiness: E2E integration and release readiness contract.

Defines the E2E flow inventory, deployment gates, and validation contracts
for the market-intelligence agent release readiness (PRODMARKET-15).

Public surface:
    * :class:`E2EFlow` -- a single E2E test flow definition (frozen dataclass).
    * :class:`E2EFlowResult` -- the result of executing an E2E flow (frozen dataclass).
    * :class:`DeploymentGate` -- a single deployment gate requirement (frozen dataclass).
    * :class:`ReleaseReadinessSpec` -- the canonical, immutable release readiness spec (frozen dataclass).
    * :class:`ReleaseReadinessError` -- raised when a flow result or readiness payload violates the contract.
    * :func:`load_release_readiness_spec` -- returns the deterministic release readiness spec.
    * :func:`validate_e2e_flow_result` -- validates a candidate E2E flow result payload.
    * :func:`validate_deployment_readiness` -- validates a candidate deployment readiness payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_FLOW_TYPES: frozenset[str] = frozenset(
    {"happy_path", "failure_path", "resiliency", "billing"}
)

_ALLOWED_STATUSES: frozenset[str] = frozenset({"passed", "failed", "skipped"})

_ALLOWED_GATE_CATEGORIES: frozenset[str] = frozenset(
    {"quality", "security", "operability", "performance"}
)

_REQUIRED_FLOW_RESULT_FIELDS: tuple[str, ...] = (
    "flow_id",
    "status",
    "executed_at",
    "evidence",
)

_REQUIRED_READINESS_FIELDS: tuple[str, ...] = (
    "gate_id",
    "passed",
    "verified_by",
    "verified_at",
)

_ROLLBACK_STEPS: tuple[str, ...] = (
    "Revert the deployment via the CI/CD rollback pipeline trigger.",
    "Restore the previous container image tag in the production manifest.",
    "Notify on-call team via PagerDuty alert and post in #incidents channel.",
    "Validate that health checks return 200 on the previous deployment.",
    "Open a post-mortem ticket and document root cause within 24 hours.",
)


class ReleaseReadinessError(ValueError):
    """Raised when a release readiness or flow result payload violates the contract."""


@dataclass(frozen=True)
class E2EFlow:
    """A single E2E test flow definition.

    Attributes:
        id: Stable identifier (e.g. ``"E2E-F1"``).
        title: Short human-readable title.
        description: One-sentence description of the flow.
        flow_type: One of ``{"happy_path", "failure_path", "resiliency", "billing"}``.
        services: Tuple of service names exercised by this flow.
    """

    id: str
    title: str
    description: str
    flow_type: str
    services: tuple[str, ...]


@dataclass(frozen=True)
class E2EFlowResult:
    """The result of executing an E2E flow.

    Attributes:
        flow_id: The id of the :class:`E2EFlow` that was executed.
        status: One of ``{"passed", "failed", "skipped"}``.
        executed_at: ISO-8601 timestamp of execution.
        evidence: Human-readable description of what was observed.
    """

    flow_id: str
    status: str
    executed_at: str
    evidence: str


@dataclass(frozen=True)
class DeploymentGate:
    """A single deployment gate requirement.

    Attributes:
        id: Stable identifier (e.g. ``"DG-1"``).
        title: Short human-readable title.
        description: One-sentence description of the gate requirement.
        category: One of ``{"quality", "security", "operability", "performance"}``.
    """

    id: str
    title: str
    description: str
    category: str


@dataclass(frozen=True)
class ReleaseReadinessSpec:
    """The canonical release readiness contract.

    Attributes:
        flows: Ordered tuple of :class:`E2EFlow` entries covering all test scenarios.
        deployment_gates: Ordered tuple of :class:`DeploymentGate` entries.
        required_readiness_fields: Tuple of field names a readiness payload must carry.
        rollback_steps: Ordered tuple of rollback procedure steps.
    """

    flows: tuple[E2EFlow, ...]
    deployment_gates: tuple[DeploymentGate, ...]
    required_readiness_fields: tuple[str, ...]
    rollback_steps: tuple[str, ...]


_CANONICAL_FLOWS: tuple[E2EFlow, ...] = (
    E2EFlow(
        id="E2E-F1",
        title="Happy Path: Live Preview to Forecast",
        description=(
            "Validates the full user journey from submitting a market observation through "
            "forecast generation, result validation, and delivery to the analyst dashboard."
        ),
        flow_type="happy_path",
        services=("market_intel", "acceptance_test_plan", "mvp_requirements"),
    ),
    E2EFlow(
        id="E2E-F2",
        title="Happy Path: Market Intensity Analysis",
        description=(
            "Verifies that a valid market symbol input produces a complete intensity analysis "
            "across volume, volatility, momentum, and sentiment signals."
        ),
        flow_type="happy_path",
        services=("market_intel", "market_intensity_agent"),
    ),
    E2EFlow(
        id="E2E-F3",
        title="Failure Path: Billing Service Unavailable",
        description=(
            "Confirms that forecast generation halts gracefully and returns an appropriate "
            "error response when the billing service returns a 402 payment-required error."
        ),
        flow_type="failure_path",
        services=("market_intel", "billing"),
    ),
    E2EFlow(
        id="E2E-F4",
        title="Failure Path: Invalid Forecast Payload Rejected",
        description=(
            "Ensures that a malformed or incomplete forecast payload is rejected by MVP "
            "validation before reaching downstream consumers."
        ),
        flow_type="failure_path",
        services=("market_intel", "mvp_requirements"),
    ),
    E2EFlow(
        id="E2E-F5",
        title="Resiliency: Retry on Transient Upstream Failure",
        description=(
            "Validates that the agent retries gracefully when an upstream data provider "
            "returns a transient 503 error, and eventually succeeds or fails fast."
        ),
        flow_type="resiliency",
        services=("market_intel", "market_intensity_agent"),
    ),
    E2EFlow(
        id="E2E-F6",
        title="Billing: Paid Call Lifecycle Verified",
        description=(
            "Validates that a successful forecast call is correctly recorded in the billing "
            "ledger, including idempotency on duplicate submission."
        ),
        flow_type="billing",
        services=("market_intel", "billing"),
    ),
)

_CANONICAL_GATES: tuple[DeploymentGate, ...] = (
    DeploymentGate(
        id="DG-1",
        title="Test Coverage and CI Gate",
        description=(
            "All automated tests (unit, integration, E2E) must pass in CI and "
            "test coverage must meet or exceed the project quality threshold."
        ),
        category="quality",
    ),
    DeploymentGate(
        id="DG-2",
        title="Security Scan and Secrets Audit",
        description=(
            "A full security scan must complete with no critical CVEs and no "
            "secrets exposed in source, environment, or container layers."
        ),
        category="security",
    ),
    DeploymentGate(
        id="DG-3",
        title="Monitoring and Alerting Verified",
        description=(
            "Dashboards, alert policies, and PagerDuty routing must be confirmed "
            "in the staging environment before production promotion is approved."
        ),
        category="operability",
    ),
    DeploymentGate(
        id="DG-4",
        title="Rollback Procedure Verified",
        description=(
            "The rollback plan must be documented, reviewed, and dry-run validated "
            "in the staging environment to confirm it restores the prior stable state."
        ),
        category="operability",
    ),
    DeploymentGate(
        id="DG-5",
        title="Performance Benchmark Gate",
        description=(
            "The service must satisfy p95 latency and throughput benchmarks under "
            "peak-load simulation before the release is promoted to production."
        ),
        category="performance",
    ),
)

_SPEC = ReleaseReadinessSpec(
    flows=_CANONICAL_FLOWS,
    deployment_gates=_CANONICAL_GATES,
    required_readiness_fields=_REQUIRED_READINESS_FIELDS,
    rollback_steps=_ROLLBACK_STEPS,
)


def load_release_readiness_spec() -> ReleaseReadinessSpec:
    """Return the canonical, immutable release readiness spec.

    Deterministic: repeated calls return equal :class:`ReleaseReadinessSpec` instances.
    """
    return _SPEC


def validate_e2e_flow_result(payload: Any) -> None:
    """Validate that ``payload`` meets the E2E flow result contract.

    Empty values are defined as ``None`` or the empty string ``""``.

    Raises:
        ReleaseReadinessError: If ``payload`` is not a dict, is missing any
            required field, has empty values, carries an unknown ``flow_id``,
            or uses a disallowed ``status``.
    """
    if not isinstance(payload, dict):
        raise ReleaseReadinessError(
            f"payload must be a dict, got {type(payload).__name__}"
        )

    violations: list[str] = []

    for field in _REQUIRED_FLOW_RESULT_FIELDS:
        if field not in payload:
            violations.append(f"missing required field: {field}")
        elif payload[field] is None or payload[field] == "":
            violations.append(f"empty required field: {field}")

    if violations:
        raise ReleaseReadinessError("; ".join(violations))

    known_ids = {f.id for f in _SPEC.flows}
    flow_id = payload["flow_id"]
    if flow_id not in known_ids:
        raise ReleaseReadinessError(
            f"unknown flow_id: {flow_id!r}; known ids: {sorted(known_ids)}"
        )

    status = payload["status"]
    if status not in _ALLOWED_STATUSES:
        raise ReleaseReadinessError(
            f"invalid status {status!r}; must be one of {sorted(_ALLOWED_STATUSES)}"
        )


def validate_deployment_readiness(payload: Any) -> None:
    """Validate that ``payload`` meets the deployment readiness contract.

    Empty values are defined as ``None`` or the empty string ``""``.

    Raises:
        ReleaseReadinessError: If ``payload`` is not a dict, is missing any
            required readiness field, or has empty values for required fields.
            All offending fields are named in the error message.
    """
    if not isinstance(payload, dict):
        raise ReleaseReadinessError(
            f"payload must be a dict, got {type(payload).__name__}"
        )

    violations: list[str] = []

    for field in _SPEC.required_readiness_fields:
        if field not in payload:
            violations.append(field)
        elif payload[field] is None or payload[field] == "":
            violations.append(field)

    if violations:
        raise ReleaseReadinessError(
            f"deployment readiness payload missing or empty required fields: "
            f"{', '.join(violations)}"
        )


__all__ = [
    "DeploymentGate",
    "E2EFlow",
    "E2EFlowResult",
    "ReleaseReadinessError",
    "ReleaseReadinessSpec",
    "load_release_readiness_spec",
    "validate_deployment_readiness",
    "validate_e2e_flow_result",
]
