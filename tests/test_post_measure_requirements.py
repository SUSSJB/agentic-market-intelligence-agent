"""Tests for the Post-Measure Requirements contract.

Test intent
-----------
These tests describe the *shape* the Post-Measure Requirements contract must
satisfy for the market-intelligence agent's post-measurement validation gate:

* ``load_post_measure_spec()`` must return a canonical, immutable
  :class:`PostMeasureSpec` with a stable set of required result fields and a
  non-empty ordered list of :class:`MeasureRequirement` entries spanning
  accuracy, completeness, timeliness, and consistency categories.
* ``validate_measure_result(payload)`` must accept any dict matching the spec's
  ``required_result_fields`` and reject non-dicts, missing fields, and empty
  required values with :class:`PostMeasureError`.

TDD history
-----------
PRODMARKET-9 introduced these tests marked ``xfail(strict=True, ...)`` so CI
stays green while the implementation ticket (PRODMARKET-10) is open.
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

from market_intel.post_measure_requirements import (
    MeasureRequirement,
    PostMeasureError,
    PostMeasureSpec,
    load_post_measure_spec,
    validate_measure_result,
)

# ---------------------------------------------------------------------------
# Dataclass shape — locks the public contract (these pass today)
# ---------------------------------------------------------------------------


def test_measure_requirement_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(MeasureRequirement)}
    assert field_names == {"id", "title", "description", "category"}
    assert MeasureRequirement.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_post_measure_spec_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(PostMeasureSpec)}
    assert field_names == {"required_result_fields", "requirements"}
    assert PostMeasureSpec.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_post_measure_error_is_valueerror_subclass():
    assert issubclass(PostMeasureError, ValueError)


def test_measure_requirement_instance_is_immutable():
    req = MeasureRequirement(id="X", title="t", description="d", category="accuracy")
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.title = "changed"  # type: ignore[misc]


def test_measure_requirement_is_hashable():
    req = MeasureRequirement(id="X", title="t", description="d", category="accuracy")
    assert hash(req) == hash(req)
    assert {req} == {req}


def test_module_exports_expected_public_symbols():
    from market_intel import post_measure_requirements

    assert set(post_measure_requirements.__all__) == {
        "MeasureRequirement",
        "PostMeasureError",
        "PostMeasureSpec",
        "load_post_measure_spec",
        "validate_measure_result",
    }


# ---------------------------------------------------------------------------
# load_post_measure_spec — behaviour tests (xfail until PRODMARKET-10)
# ---------------------------------------------------------------------------



def test_load_post_measure_spec_returns_spec_instance():
    spec = load_post_measure_spec()
    assert isinstance(spec, PostMeasureSpec)


def test_load_post_measure_spec_declares_required_result_fields():
    spec = load_post_measure_spec()
    expected = {
        "measure_id",
        "metric_value",
        "measured_at",
        "data_source",
        "confidence_score",
    }
    assert expected.issubset(set(spec.required_result_fields)), (
        f"required_result_fields must cover {expected}, "
        f"got {spec.required_result_fields}"
    )


def test_load_post_measure_spec_has_non_empty_ordered_requirements():
    spec = load_post_measure_spec()
    assert isinstance(spec.requirements, tuple)
    assert len(spec.requirements) >= 1
    assert all(isinstance(r, MeasureRequirement) for r in spec.requirements)


def test_load_post_measure_spec_requirement_ids_are_unique_and_non_empty():
    spec = load_post_measure_spec()
    ids = [r.id for r in spec.requirements]
    assert all(rid for rid in ids), "requirement ids must be non-empty"
    assert len(ids) == len(set(ids)), f"requirement ids must be unique, got {ids}"


def test_load_post_measure_spec_categories_are_from_allowed_set():
    spec = load_post_measure_spec()
    allowed = {"accuracy", "completeness", "timeliness", "consistency"}
    bad = [r for r in spec.requirements if r.category not in allowed]
    assert not bad, f"requirements with disallowed category: {bad}"


def test_load_post_measure_spec_covers_all_allowed_categories():
    spec = load_post_measure_spec()
    categories = {r.category for r in spec.requirements}
    assert categories == {"accuracy", "completeness", "timeliness", "consistency"}


def test_load_post_measure_spec_requirement_titles_and_descriptions_non_empty():
    spec = load_post_measure_spec()
    for r in spec.requirements:
        assert r.title.strip(), f"requirement {r.id} has empty title"
        assert r.description.strip(), f"requirement {r.id} has empty description"


def test_load_post_measure_spec_is_deterministic_across_calls():
    assert load_post_measure_spec() == load_post_measure_spec()


def test_load_post_measure_spec_repeated_calls_have_equal_requirements():
    a = load_post_measure_spec()
    b = load_post_measure_spec()
    assert a.requirements == b.requirements
    assert a.required_result_fields == b.required_result_fields


def test_load_post_measure_spec_field_containers_are_tuples():
    spec = load_post_measure_spec()
    assert isinstance(spec.required_result_fields, tuple)
    assert isinstance(spec.requirements, tuple)


def test_post_measure_spec_instance_is_immutable():
    spec = load_post_measure_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.required_result_fields = ()  # type: ignore[misc]


def test_load_post_measure_spec_contains_canonical_requirement_ids():
    spec = load_post_measure_spec()
    ids = {r.id for r in spec.requirements}
    assert {"PMR-R1", "PMR-R2", "PMR-R3", "PMR-R4"}.issubset(ids)


def test_load_post_measure_spec_has_accuracy_requirement():
    spec = load_post_measure_spec()
    accuracy_reqs = [r for r in spec.requirements if r.category == "accuracy"]
    assert accuracy_reqs, "spec must include at least one accuracy requirement"
    text = " ".join((r.title + " " + r.description).lower() for r in accuracy_reqs)
    assert any(kw in text for kw in ("accura", "precision", "correct", "valid"))


def test_load_post_measure_spec_has_completeness_requirement():
    spec = load_post_measure_spec()
    completeness_reqs = [r for r in spec.requirements if r.category == "completeness"]
    assert completeness_reqs, "spec must include at least one completeness requirement"
    text = " ".join(
        (r.title + " " + r.description).lower() for r in completeness_reqs
    )
    assert any(kw in text for kw in ("complet", "missing", "coverage", "full"))


def test_load_post_measure_spec_has_timeliness_requirement():
    spec = load_post_measure_spec()
    timeliness_reqs = [r for r in spec.requirements if r.category == "timeliness"]
    assert timeliness_reqs, "spec must include at least one timeliness requirement"
    text = " ".join(
        (r.title + " " + r.description).lower() for r in timeliness_reqs
    )
    assert any(kw in text for kw in ("time", "latenc", "freshn", "staleness", "delay"))


def test_load_post_measure_spec_has_consistency_requirement():
    spec = load_post_measure_spec()
    consistency_reqs = [r for r in spec.requirements if r.category == "consistency"]
    assert consistency_reqs, "spec must include at least one consistency requirement"
    text = " ".join(
        (r.title + " " + r.description).lower() for r in consistency_reqs
    )
    assert any(kw in text for kw in ("consist", "reproducib", "determin", "stable"))


# ---------------------------------------------------------------------------
# validate_measure_result — behaviour tests (xfail until PRODMARKET-10)
# ---------------------------------------------------------------------------


def test_validate_measure_result_accepts_payload_with_all_required_fields():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    validate_measure_result(payload)  # must not raise


def test_validate_measure_result_accepts_payload_with_extra_fields():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload["debug_note"] = "extra field is fine"
    validate_measure_result(payload)


@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "result", 42, 3.14, ("measure_id", "metric_value")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_validate_measure_result_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(PostMeasureError):
        validate_measure_result(not_a_dict)  # type: ignore[arg-type]


def test_validate_measure_result_non_dict_error_names_actual_type():
    with pytest.raises(PostMeasureError) as exc_info:
        validate_measure_result("not a dict")  # type: ignore[arg-type]
    assert "str" in str(exc_info.value)


def test_validate_measure_result_rejects_missing_required_field():
    spec = load_post_measure_spec()
    assert spec.required_result_fields, "spec must have at least one required field"
    missing = spec.required_result_fields[0]
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    del payload[missing]

    with pytest.raises(PostMeasureError) as exc_info:
        validate_measure_result(payload)
    assert missing in str(exc_info.value)


def test_validate_measure_result_rejects_empty_required_value():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload[spec.required_result_fields[0]] = ""

    with pytest.raises(PostMeasureError):
        validate_measure_result(payload)


def test_validate_measure_result_rejects_none_required_value():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload[spec.required_result_fields[0]] = None

    with pytest.raises(PostMeasureError):
        validate_measure_result(payload)


def test_validate_measure_result_rejects_all_fields_missing():
    with pytest.raises(PostMeasureError) as exc_info:
        validate_measure_result({})
    msg = str(exc_info.value)
    spec = load_post_measure_spec()
    for field in spec.required_result_fields:
        assert field in msg


def test_validate_measure_result_reports_multiple_missing_fields():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    dropped = list(spec.required_result_fields[:2])
    for f in dropped:
        del payload[f]

    with pytest.raises(PostMeasureError) as exc_info:
        validate_measure_result(payload)
    msg = str(exc_info.value)
    for f in dropped:
        assert f in msg


def test_validate_measure_result_reports_multiple_empty_fields():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload[spec.required_result_fields[0]] = ""
    payload[spec.required_result_fields[1]] = None

    with pytest.raises(PostMeasureError) as exc_info:
        validate_measure_result(payload)
    msg = str(exc_info.value)
    assert spec.required_result_fields[0] in msg
    assert spec.required_result_fields[1] in msg


def test_validate_measure_result_accepts_non_string_non_empty_values():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload["metric_value"] = 42.7
    payload["confidence_score"] = 0.95
    validate_measure_result(payload)


def test_validate_measure_result_accepts_whitespace_string_values():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload[spec.required_result_fields[0]] = " "
    validate_measure_result(payload)


def test_validate_measure_result_accepts_zero_and_false_values():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload["metric_value"] = 0
    payload["confidence_score"] = 0.0
    validate_measure_result(payload)


def test_validate_measure_result_does_not_mutate_payload():
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    snapshot = dict(payload)
    try:
        validate_measure_result(payload)
    except (PostMeasureError, NotImplementedError):
        pass
    assert payload == snapshot


# ---------------------------------------------------------------------------
# Additional contract tests
# ---------------------------------------------------------------------------


def test_measure_requirement_equality_between_equal_instances():
    a = MeasureRequirement(id="P1", title="t", description="d", category="accuracy")
    b = MeasureRequirement(id="P1", title="t", description="d", category="accuracy")
    assert a == b


def test_measure_requirement_inequality_between_different_instances():
    a = MeasureRequirement(id="P1", title="t", description="d", category="accuracy")
    b = MeasureRequirement(id="P2", title="t", description="d", category="accuracy")
    assert a != b


def test_post_measure_error_carries_message():
    msg = "missing field: measure_id"
    err = PostMeasureError(msg)
    assert str(err) == msg


def test_post_measure_error_is_catchable_as_valueerror():
    with pytest.raises(ValueError):
        raise PostMeasureError("bad payload")


# ---------------------------------------------------------------------------
# Additional edge-case tests (PRODMARKET-10)
# ---------------------------------------------------------------------------


def test_validate_measure_result_accepts_false_as_field_value():
    """False is explicitly listed as accepted in the module docstring."""
    spec = load_post_measure_spec()
    payload = {name: f"value-{name}" for name in spec.required_result_fields}
    payload["confidence_score"] = False
    validate_measure_result(payload)  # must not raise


def test_validate_measure_result_error_message_mentions_missing_or_empty():
    spec = load_post_measure_spec()
    with pytest.raises(PostMeasureError) as exc_info:
        validate_measure_result({})
    msg = str(exc_info.value).lower()
    assert "missing" in msg or "empty" in msg


def test_post_measure_spec_is_hashable():
    spec = load_post_measure_spec()
    assert hash(spec) == hash(spec)
    assert {spec} == {spec}


def test_validate_measure_result_rejects_each_individual_required_field_missing():
    """Each required field, when individually absent, raises PostMeasureError naming it."""
    spec = load_post_measure_spec()
    for field in spec.required_result_fields:
        payload = {name: f"value-{name}" for name in spec.required_result_fields}
        del payload[field]
        with pytest.raises(PostMeasureError) as exc_info:
            validate_measure_result(payload)
        assert field in str(exc_info.value), f"error message must name missing field '{field}'"


def test_validate_measure_result_rejects_each_individual_required_field_empty_string():
    """Each required field set individually to '' raises PostMeasureError naming it."""
    spec = load_post_measure_spec()
    for field in spec.required_result_fields:
        payload = {name: f"value-{name}" for name in spec.required_result_fields}
        payload[field] = ""
        with pytest.raises(PostMeasureError) as exc_info:
            validate_measure_result(payload)
        assert field in str(exc_info.value), f"error message must name empty field '{field}'"


def test_validate_measure_result_rejects_each_individual_required_field_none():
    """Each required field set individually to None raises PostMeasureError naming it."""
    spec = load_post_measure_spec()
    for field in spec.required_result_fields:
        payload = {name: f"value-{name}" for name in spec.required_result_fields}
        payload[field] = None
        with pytest.raises(PostMeasureError) as exc_info:
            validate_measure_result(payload)
        assert field in str(exc_info.value), f"error message must name None field '{field}'"


def test_load_post_measure_spec_required_fields_are_non_empty_strings():
    spec = load_post_measure_spec()
    for field in spec.required_result_fields:
        assert isinstance(field, str) and field.strip(), (
            f"required field name must be non-empty string, got {field!r}"
        )


def test_measure_requirement_all_fields_are_non_empty_strings_on_canonical_spec():
    spec = load_post_measure_spec()
    for req in spec.requirements:
        assert isinstance(req.id, str) and req.id.strip()
        assert isinstance(req.title, str) and req.title.strip()
        assert isinstance(req.description, str) and req.description.strip()
        assert isinstance(req.category, str) and req.category.strip()
