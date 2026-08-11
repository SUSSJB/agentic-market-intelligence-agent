"""Production Release Requirements: canonical release-gate contract.

Defines the shape of the Production Release Requirements contract for the
market-intelligence agent — covering quality, performance, security, and
operability gates that must pass before a production deployment is approved.

Public surface:
    * :class:`ReleaseRequirement` — a single release gate requirement (frozen dataclass).
    * :class:`ProductionReleaseSpec` — the canonical, immutable release spec (frozen dataclass).
    * :class:`ReleaseRequirementsError` — raised when a readiness payload violates the contract.
    * :func:`load_production_release_spec` — returns the deterministic release spec.
    * :func:`validate_release_readiness` — validates a candidate release readiness payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"quality", "performance", "security", "operability"}
)


class ReleaseRequirementsError(ValueError):
    """Raised when a release spec or readiness payload violates the contract."""


@dataclass(frozen=True)
class ReleaseRequirement:
    """A single production release gate requirement.

    Attributes:
        id: Stable identifier (e.g. ``"PRR-R1"``).
        title: Short human-readable title.
        description: One-sentence description of the requirement.
        category: One of ``{"quality", "performance", "security", "operability"}``.
    """

    id: str
    title: str
    description: str
    category: str


@dataclass(frozen=True)
class ProductionReleaseSpec:
    """The canonical production release requirements contract.

    Attributes:
        required_readiness_fields: Tuple of field names a readiness payload must carry
            (e.g. ``"release_id"``, ``"test_coverage_pct"``, ``"security_scan_passed"``,
            ``"performance_benchmark_passed"``, ``"approved_by"``).
        requirements: Ordered tuple of :class:`ReleaseRequirement` entries.
    """

    required_readiness_fields: tuple[str, ...]
    requirements: tuple[ReleaseRequirement, ...]


def load_production_release_spec() -> ProductionReleaseSpec:
    """Return the canonical, immutable production release spec.

    Deterministic: repeated calls return equal :class:`ProductionReleaseSpec` instances.

    Raises:
        NotImplementedError: Until PRODMARKET-8 delivers the implementation.
    """
    raise NotImplementedError(
        "load_production_release_spec() is pending PRODMARKET-8 implementation"
    )


def validate_release_readiness(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` meets the production release readiness contract.

    Raises:
        ReleaseRequirementsError: If ``payload`` is not a dict, is missing any
            required readiness field, or has empty values (``None`` or empty
            string) for required fields.
        NotImplementedError: Until PRODMARKET-8 delivers the implementation.
    """
    raise NotImplementedError(
        "validate_release_readiness() is pending PRODMARKET-8 implementation"
    )


__all__ = [
    "ProductionReleaseSpec",
    "ReleaseRequirement",
    "ReleaseRequirementsError",
    "load_production_release_spec",
    "validate_release_readiness",
]
