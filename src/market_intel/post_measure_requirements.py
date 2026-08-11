"""Post-Measure Requirements: canonical post-measurement validation contract.

Defines the shape of the Post-Measure Requirements contract for the
market-intelligence agent — covering accuracy, completeness, timeliness, and
consistency gates that must pass after market measurements are taken.

Public surface:
    * :class:`MeasureRequirement` — a single post-measure requirement (frozen dataclass).
    * :class:`PostMeasureSpec` — the canonical, immutable post-measure spec (frozen dataclass).
    * :class:`PostMeasureError` — raised when a measure result payload violates the contract.
    * :func:`load_post_measure_spec` — returns the deterministic post-measure spec.
    * :func:`validate_measure_result` — validates a candidate measure result payload.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"accuracy", "completeness", "timeliness", "consistency"}
)

_REQUIRED_RESULT_FIELDS: tuple[str, ...] = (
    "measure_id",
    "metric_value",
    "measured_at",
    "data_source",
    "confidence_score",
)


class PostMeasureError(ValueError):
    """Raised when a post-measure spec or result payload violates the contract."""


@dataclass(frozen=True)
class MeasureRequirement:
    """A single post-measure requirement.

    Attributes:
        id: Stable identifier (e.g. ``"PMR-R1"``).
        title: Short human-readable title.
        description: One-sentence description of the requirement.
        category: One of ``{"accuracy", "completeness", "timeliness", "consistency"}``.
    """

    id: str
    title: str
    description: str
    category: str


@dataclass(frozen=True)
class PostMeasureSpec:
    """The canonical post-measure requirements contract.

    Attributes:
        required_result_fields: Tuple of field names a measure result payload must carry
            (e.g. ``"measure_id"``, ``"metric_value"``, ``"measured_at"``,
            ``"data_source"``, ``"confidence_score"``).
        requirements: Ordered tuple of :class:`MeasureRequirement` entries.
    """

    required_result_fields: tuple[str, ...]
    requirements: tuple[MeasureRequirement, ...]


_CANONICAL_REQUIREMENTS: tuple[MeasureRequirement, ...] = (
    MeasureRequirement(
        id="PMR-R1",
        title="Measurement Accuracy Gate",
        description=(
            "Each market measurement must be validated for accuracy and correctness "
            "against known reference values or precision thresholds before being accepted."
        ),
        category="accuracy",
    ),
    MeasureRequirement(
        id="PMR-R2",
        title="Data Completeness Gate",
        description=(
            "All required fields of a measurement result must be present with no missing "
            "or null values to ensure full coverage of the market data contract."
        ),
        category="completeness",
    ),
    MeasureRequirement(
        id="PMR-R3",
        title="Measurement Timeliness Gate",
        description=(
            "Market measurements must meet freshness and staleness thresholds so that "
            "time-sensitive financial analysis is never performed on delayed data."
        ),
        category="timeliness",
    ),
    MeasureRequirement(
        id="PMR-R4",
        title="Result Consistency Gate",
        description=(
            "Repeated measurements under identical conditions must produce consistent and "
            "deterministically stable results to support reproducible financial analysis."
        ),
        category="consistency",
    ),
)


def load_post_measure_spec() -> PostMeasureSpec:
    """Return the canonical, immutable post-measure spec.

    Deterministic: repeated calls return equal :class:`PostMeasureSpec` instances.
    """
    return PostMeasureSpec(
        required_result_fields=_REQUIRED_RESULT_FIELDS,
        requirements=_CANONICAL_REQUIREMENTS,
    )


def validate_measure_result(payload: dict[str, Any]) -> None:
    """Validate that ``payload`` meets the post-measure result contract.

    Empty values are defined as ``None`` or the empty string ``""``.
    Whitespace-only strings, ``0``, and ``False`` are accepted.

    Raises:
        PostMeasureError: If ``payload`` is not a dict, is missing any
            required result field, or has empty values (``None`` or empty
            string) for required fields.
    """
    if not isinstance(payload, dict):
        raise PostMeasureError(
            f"payload must be a dict, got {type(payload).__name__}"
        )

    spec = load_post_measure_spec()
    violations: list[str] = []

    for field in spec.required_result_fields:
        if field not in payload:
            violations.append(field)
        elif payload[field] is None or payload[field] == "":
            violations.append(field)

    if violations:
        raise PostMeasureError(
            f"measure result payload missing or empty required fields: "
            f"{', '.join(violations)}"
        )


__all__ = [
    "MeasureRequirement",
    "PostMeasureError",
    "PostMeasureSpec",
    "load_post_measure_spec",
    "validate_measure_result",
]
