"""Tests for the Implementation Roadmap contract.

Test intent
-----------
These tests describe the *shape* the Implementation Roadmap contract must
satisfy for the market-intelligence agent's milestone delivery tracking:

* ``load_implementation_roadmap()`` must return a canonical, immutable
  :class:`ImplementationRoadmap` with a stable set of required progress fields,
  a non-empty ordered list of :class:`RoadmapMilestone` entries spanning all
  four delivery phases (planning, development, testing, deployment), and a
  version string.
* ``validate_roadmap_progress(payload)`` must accept any dict matching the
  roadmap's ``required_progress_fields`` with a known ``milestone_id`` and a
  valid ``status``, and reject non-dicts, missing fields, empty required values,
  unknown milestone ids, and disallowed statuses with :class:`RoadmapError`.

TDD history
-----------
PRODMARKET-13 introduced these tests marked ``xfail(strict=True, ...)`` so CI
stays green while the implementation ticket (PRODMARKET-14) is open.
Once the implementation makes any xfail test pass, ``strict=True`` flips it
to XPASS and turns CI red — forcing the follow-up PR to actually remove the
pending markers.

External deps
-------------
None. Everything is exercised in-process — the module has no I/O and no
network calls, so no mocking is needed.
"""
from __future__ import annotations

import dataclasses

import pytest

from market_intel.implementation_roadmap import (
    ImplementationRoadmap,
    RoadmapError,
    RoadmapMilestone,
    load_implementation_roadmap,
    validate_roadmap_progress,
)

# ---------------------------------------------------------------------------
# Dataclass shape — locks the public contract (these pass today)
# ---------------------------------------------------------------------------


def test_roadmap_milestone_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(RoadmapMilestone)}
    assert field_names == {"id", "title", "description", "phase", "priority", "dependencies"}
    assert RoadmapMilestone.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_implementation_roadmap_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(ImplementationRoadmap)}
    assert field_names == {"required_progress_fields", "milestones", "version"}
    assert ImplementationRoadmap.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_roadmap_error_is_valueerror_subclass():
    assert issubclass(RoadmapError, ValueError)


def test_roadmap_milestone_instance_is_immutable():
    m = RoadmapMilestone(
        id="RM-M1", title="t", description="d",
        phase="planning", priority="high", dependencies=()
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.title = "changed"  # type: ignore[misc]


def test_roadmap_milestone_is_hashable():
    m = RoadmapMilestone(
        id="RM-M1", title="t", description="d",
        phase="planning", priority="high", dependencies=()
    )
    assert hash(m) == hash(m)
    assert {m} == {m}


def test_module_exports_expected_public_symbols():
    from market_intel import implementation_roadmap

    assert set(implementation_roadmap.__all__) == {
        "ImplementationRoadmap",
        "RoadmapError",
        "RoadmapMilestone",
        "load_implementation_roadmap",
        "validate_roadmap_progress",
    }


def test_roadmap_milestone_equality_between_equal_instances():
    a = RoadmapMilestone(
        id="RM-M1", title="t", description="d",
        phase="planning", priority="high", dependencies=()
    )
    b = RoadmapMilestone(
        id="RM-M1", title="t", description="d",
        phase="planning", priority="high", dependencies=()
    )
    assert a == b


def test_roadmap_milestone_inequality_between_different_instances():
    a = RoadmapMilestone(
        id="RM-M1", title="t", description="d",
        phase="planning", priority="high", dependencies=()
    )
    b = RoadmapMilestone(
        id="RM-M2", title="t", description="d",
        phase="planning", priority="high", dependencies=()
    )
    assert a != b


def test_roadmap_error_carries_message():
    msg = "missing field: milestone_id"
    err = RoadmapError(msg)
    assert str(err) == msg


def test_roadmap_error_is_catchable_as_valueerror():
    with pytest.raises(ValueError):
        raise RoadmapError("bad payload")


# ---------------------------------------------------------------------------
# load_implementation_roadmap — behaviour tests (xfail until PRODMARKET-14)
# ---------------------------------------------------------------------------


def test_load_implementation_roadmap_returns_roadmap_instance():
    roadmap = load_implementation_roadmap()
    assert isinstance(roadmap, ImplementationRoadmap)


def test_load_implementation_roadmap_has_non_empty_milestones():
    roadmap = load_implementation_roadmap()
    assert isinstance(roadmap.milestones, tuple)
    assert len(roadmap.milestones) >= 1
    assert all(isinstance(m, RoadmapMilestone) for m in roadmap.milestones)


def test_load_implementation_roadmap_milestone_ids_are_unique_and_non_empty():
    roadmap = load_implementation_roadmap()
    ids = [m.id for m in roadmap.milestones]
    assert all(mid for mid in ids), "milestone ids must be non-empty"
    assert len(ids) == len(set(ids)), f"milestone ids must be unique, got {ids}"


def test_load_implementation_roadmap_phases_are_from_allowed_set():
    roadmap = load_implementation_roadmap()
    allowed = {"planning", "development", "testing", "deployment"}
    bad = [m for m in roadmap.milestones if m.phase not in allowed]
    assert not bad, f"milestones with disallowed phase: {bad}"


def test_load_implementation_roadmap_covers_all_phases():
    roadmap = load_implementation_roadmap()
    phases = {m.phase for m in roadmap.milestones}
    assert phases == {"planning", "development", "testing", "deployment"}


def test_load_implementation_roadmap_priorities_are_from_allowed_set():
    roadmap = load_implementation_roadmap()
    allowed = {"high", "medium", "low"}
    bad = [m for m in roadmap.milestones if m.priority not in allowed]
    assert not bad, f"milestones with disallowed priority: {bad}"


def test_load_implementation_roadmap_has_at_least_one_high_priority_milestone():
    roadmap = load_implementation_roadmap()
    high_priority = [m for m in roadmap.milestones if m.priority == "high"]
    assert high_priority, "roadmap must include at least one high priority milestone"


def test_load_implementation_roadmap_milestone_titles_and_descriptions_non_empty():
    roadmap = load_implementation_roadmap()
    for m in roadmap.milestones:
        assert m.title.strip(), f"milestone {m.id} has empty title"
        assert m.description.strip(), f"milestone {m.id} has empty description"


def test_load_implementation_roadmap_is_deterministic_across_calls():
    assert load_implementation_roadmap() == load_implementation_roadmap()


def test_load_implementation_roadmap_repeated_calls_have_equal_milestones():
    a = load_implementation_roadmap()
    b = load_implementation_roadmap()
    assert a.milestones == b.milestones
    assert a.required_progress_fields == b.required_progress_fields
    assert a.version == b.version


def test_load_implementation_roadmap_field_containers_are_tuples():
    roadmap = load_implementation_roadmap()
    assert isinstance(roadmap.required_progress_fields, tuple)
    assert isinstance(roadmap.milestones, tuple)


def test_load_implementation_roadmap_instance_is_immutable():
    roadmap = load_implementation_roadmap()
    with pytest.raises(dataclasses.FrozenInstanceError):
        roadmap.required_progress_fields = ()  # type: ignore[misc]


def test_load_implementation_roadmap_has_version_string():
    roadmap = load_implementation_roadmap()
    assert isinstance(roadmap.version, str)
    assert roadmap.version.strip(), "version must be non-empty"


def test_load_implementation_roadmap_declares_required_progress_fields():
    roadmap = load_implementation_roadmap()
    expected = {"milestone_id", "status", "completed_at", "owner", "evidence"}
    assert expected.issubset(set(roadmap.required_progress_fields)), (
        f"required_progress_fields must cover {expected}, "
        f"got {roadmap.required_progress_fields}"
    )


def test_load_implementation_roadmap_contains_canonical_milestone_ids():
    roadmap = load_implementation_roadmap()
    ids = {m.id for m in roadmap.milestones}
    assert {"RM-M1", "RM-M2", "RM-M3", "RM-M4"}.issubset(ids)


def test_load_implementation_roadmap_has_planning_milestone():
    roadmap = load_implementation_roadmap()
    planning = [m for m in roadmap.milestones if m.phase == "planning"]
    assert planning, "roadmap must include at least one planning phase milestone"
    text = " ".join((m.title + " " + m.description).lower() for m in planning)
    assert any(kw in text for kw in ("plan", "design", "architect", "require", "scope"))


def test_load_implementation_roadmap_has_development_milestone():
    roadmap = load_implementation_roadmap()
    dev = [m for m in roadmap.milestones if m.phase == "development"]
    assert dev, "roadmap must include at least one development phase milestone"
    text = " ".join((m.title + " " + m.description).lower() for m in dev)
    assert any(kw in text for kw in ("develop", "implement", "build", "code", "feature"))


def test_load_implementation_roadmap_has_testing_milestone():
    roadmap = load_implementation_roadmap()
    testing = [m for m in roadmap.milestones if m.phase == "testing"]
    assert testing, "roadmap must include at least one testing phase milestone"
    text = " ".join((m.title + " " + m.description).lower() for m in testing)
    assert any(kw in text for kw in ("test", "verif", "valid", "qa", "quality"))


def test_load_implementation_roadmap_has_deployment_milestone():
    roadmap = load_implementation_roadmap()
    deployment = [m for m in roadmap.milestones if m.phase == "deployment"]
    assert deployment, "roadmap must include at least one deployment phase milestone"
    text = " ".join((m.title + " " + m.description).lower() for m in deployment)
    assert any(kw in text for kw in ("deploy", "release", "ship", "launch", "produc"))


def test_load_implementation_roadmap_dependencies_are_tuples():
    roadmap = load_implementation_roadmap()
    for m in roadmap.milestones:
        assert isinstance(m.dependencies, tuple), (
            f"milestone {m.id} dependencies must be a tuple, got {type(m.dependencies)}"
        )


def test_load_implementation_roadmap_dependency_ids_reference_known_milestones():
    roadmap = load_implementation_roadmap()
    all_ids = {m.id for m in roadmap.milestones}
    for m in roadmap.milestones:
        for dep_id in m.dependencies:
            assert dep_id in all_ids, (
                f"milestone {m.id} depends on unknown id {dep_id!r}"
            )


# ---------------------------------------------------------------------------
# validate_roadmap_progress — behaviour tests (xfail until PRODMARKET-14)
# ---------------------------------------------------------------------------


def test_validate_roadmap_progress_accepts_payload_with_all_required_fields():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    validate_roadmap_progress(payload)  # must not raise


def test_validate_roadmap_progress_accepts_payload_with_extra_fields():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    payload["debug_note"] = "extra field is fine"
    validate_roadmap_progress(payload)


@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "progress", 42, 3.14, ("milestone_id", "status")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_validate_roadmap_progress_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(RoadmapError):
        validate_roadmap_progress(not_a_dict)  # type: ignore[arg-type]


def test_validate_roadmap_progress_non_dict_error_names_actual_type():
    with pytest.raises(RoadmapError) as exc_info:
        validate_roadmap_progress("not a dict")  # type: ignore[arg-type]
    assert "str" in str(exc_info.value)


def test_validate_roadmap_progress_rejects_missing_required_field():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    missing = roadmap.required_progress_fields[0]
    del payload[missing]
    with pytest.raises(RoadmapError) as exc_info:
        validate_roadmap_progress(payload)
    assert missing in str(exc_info.value)


def test_validate_roadmap_progress_rejects_empty_required_value():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    payload[roadmap.required_progress_fields[-1]] = ""
    with pytest.raises(RoadmapError):
        validate_roadmap_progress(payload)


def test_validate_roadmap_progress_rejects_none_required_value():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    payload[roadmap.required_progress_fields[-1]] = None
    with pytest.raises(RoadmapError):
        validate_roadmap_progress(payload)


def test_validate_roadmap_progress_rejects_all_fields_missing():
    with pytest.raises(RoadmapError) as exc_info:
        validate_roadmap_progress({})
    msg = str(exc_info.value)
    roadmap = load_implementation_roadmap()
    for field in roadmap.required_progress_fields:
        assert field in msg


def test_validate_roadmap_progress_rejects_unknown_milestone_id():
    roadmap = load_implementation_roadmap()
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = "RM-UNKNOWN-999"
    payload["status"] = "completed"
    with pytest.raises(RoadmapError) as exc_info:
        validate_roadmap_progress(payload)
    assert "RM-UNKNOWN-999" in str(exc_info.value)


def test_validate_roadmap_progress_rejects_disallowed_status():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "invalid_status"
    with pytest.raises(RoadmapError):
        validate_roadmap_progress(payload)


def test_validate_roadmap_progress_reports_multiple_missing_fields():
    roadmap = load_implementation_roadmap()
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    dropped = list(roadmap.required_progress_fields[:2])
    for f in dropped:
        del payload[f]
    with pytest.raises(RoadmapError) as exc_info:
        validate_roadmap_progress(payload)
    msg = str(exc_info.value)
    for f in dropped:
        assert f in msg


def test_validate_roadmap_progress_accepts_valid_statuses():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    for status in ("planned", "in_progress", "completed", "blocked"):
        payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
        payload["milestone_id"] = milestone_id
        payload["status"] = status
        validate_roadmap_progress(payload)  # must not raise


def test_validate_roadmap_progress_accepts_whitespace_string_values():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    payload["evidence"] = "  "
    validate_roadmap_progress(payload)


def test_validate_roadmap_progress_does_not_mutate_payload():
    roadmap = load_implementation_roadmap()
    milestone_id = roadmap.milestones[0].id
    payload = {name: f"value-{name}" for name in roadmap.required_progress_fields}
    payload["milestone_id"] = milestone_id
    payload["status"] = "completed"
    snapshot = dict(payload)
    try:
        validate_roadmap_progress(payload)
    except (RoadmapError, NotImplementedError):
        pass
    assert payload == snapshot
