"""Implementation Roadmap: canonical milestone and progress tracking contract.

Defines the shape of the Implementation Roadmap contract for the
market-intelligence agent — covering the ordered set of delivery milestones,
their phases, priorities, and the progress validation gate applied to each
milestone's completion payload.

Public surface:
    * :class:`RoadmapMilestone` — a single roadmap milestone (frozen dataclass).
    * :class:`ImplementationRoadmap` — the canonical, immutable roadmap (frozen dataclass).
    * :class:`RoadmapError` — raised when a progress payload violates the contract.
    * :func:`load_implementation_roadmap` — returns the deterministic roadmap.
    * :func:`validate_roadmap_progress` — validates a candidate milestone progress payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_PHASES: frozenset[str] = frozenset(
    {"planning", "development", "testing", "deployment"}
)

_ALLOWED_STATUSES: frozenset[str] = frozenset(
    {"planned", "in_progress", "completed", "blocked"}
)

_ALLOWED_PRIORITIES: frozenset[str] = frozenset({"high", "medium", "low"})

_REQUIRED_PROGRESS_FIELDS: tuple[str, ...] = (
    "milestone_id",
    "status",
    "completed_at",
    "owner",
    "evidence",
)


class RoadmapError(ValueError):
    """Raised when a roadmap or progress payload violates the contract."""


@dataclass(frozen=True)
class RoadmapMilestone:
    """A single implementation roadmap milestone.

    Attributes:
        id: Stable identifier (e.g. ``"RM-M1"``).
        title: Short human-readable title.
        description: One-sentence description of the milestone.
        phase: One of ``{"planning", "development", "testing", "deployment"}``.
        priority: One of ``{"high", "medium", "low"}``.
        dependencies: Tuple of milestone ids this milestone depends on.
    """

    id: str
    title: str
    description: str
    phase: str
    priority: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class ImplementationRoadmap:
    """The canonical implementation roadmap contract.

    Attributes:
        required_progress_fields: Tuple of field names a progress payload must carry
            (e.g. ``"milestone_id"``, ``"status"``, ``"completed_at"``,
            ``"owner"``, ``"evidence"``).
        milestones: Ordered tuple of :class:`RoadmapMilestone` entries.
        version: Semantic version string for the roadmap schema.
    """

    required_progress_fields: tuple[str, ...]
    milestones: tuple[RoadmapMilestone, ...]
    version: str


_MILESTONES: tuple[RoadmapMilestone, ...] = (
    RoadmapMilestone(
        id="RM-M1",
        title="Requirements and Architecture Design",
        description=(
            "Plan and architect the market-intelligence agent scope, define the "
            "requirements contract, and produce the high-level design document."
        ),
        phase="planning",
        priority="high",
        dependencies=(),
    ),
    RoadmapMilestone(
        id="RM-M2",
        title="Core Feature Development",
        description=(
            "Implement the core market-intelligence features including OHLCV "
            "ingestion, forecast model, and all MVP requirements for financial "
            "analysts to receive detailed market movement insights."
        ),
        phase="development",
        priority="high",
        dependencies=("RM-M1",),
    ),
    RoadmapMilestone(
        id="RM-M3",
        title="Quality Assurance and Test Verification",
        description=(
            "Execute the full acceptance test plan, validate all test cases, "
            "and verify that quality requirements are satisfied across all "
            "edge cases and regression scenarios."
        ),
        phase="testing",
        priority="medium",
        dependencies=("RM-M2",),
    ),
    RoadmapMilestone(
        id="RM-M4",
        title="Production Deployment and Release",
        description=(
            "Deploy the market-intelligence agent to production, ship the release "
            "package, and launch monitoring for live market data feeds."
        ),
        phase="deployment",
        priority="high",
        dependencies=("RM-M3",),
    ),
)

_ROADMAP: ImplementationRoadmap = ImplementationRoadmap(
    required_progress_fields=_REQUIRED_PROGRESS_FIELDS,
    milestones=_MILESTONES,
    version="1.0.0",
)


def load_implementation_roadmap() -> ImplementationRoadmap:
    """Return the canonical, immutable implementation roadmap.

    Deterministic: repeated calls return equal :class:`ImplementationRoadmap` instances.
    """
    return _ROADMAP


def validate_roadmap_progress(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` meets the milestone progress contract.

    Empty values are defined as ``None`` or the empty string ``""``.
    Whitespace-only strings, ``0``, and ``False`` are accepted.

    Raises:
        RoadmapError: If ``payload`` is not a dict, is missing any required
            progress field, has empty values for required fields, contains an
            unknown ``milestone_id``, or carries a disallowed ``status``.
    """
    if not isinstance(payload, dict):
        raise RoadmapError(
            f"progress payload must be a dict, got {type(payload).__name__}"
        )

    roadmap = load_implementation_roadmap()

    missing = [f for f in roadmap.required_progress_fields if f not in payload]
    if missing:
        raise RoadmapError(
            f"progress payload missing required field(s): {', '.join(missing)}"
        )

    empty = [
        f
        for f in roadmap.required_progress_fields
        if payload[f] is None or (isinstance(payload[f], str) and payload[f] == "")
    ]
    if empty:
        raise RoadmapError(
            f"progress payload has empty value(s) for required field(s): "
            f"{', '.join(empty)}"
        )

    known_ids = {m.id for m in roadmap.milestones}
    milestone_id = payload.get("milestone_id")
    if milestone_id not in known_ids:
        raise RoadmapError(
            f"progress payload references unknown milestone_id: {milestone_id!r}"
        )

    status = payload.get("status")
    if status not in _ALLOWED_STATUSES:
        raise RoadmapError(
            f"progress payload status {status!r} is not allowed; "
            f"must be one of {sorted(_ALLOWED_STATUSES)}"
        )


__all__ = [
    "ImplementationRoadmap",
    "RoadmapError",
    "RoadmapMilestone",
    "load_implementation_roadmap",
    "validate_roadmap_progress",
]
