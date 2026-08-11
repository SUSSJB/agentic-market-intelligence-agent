"""Tests for the MVP Requirements contract.

Test intent
-----------
These tests describe the *shape* the MVP contract must satisfy for the
market-intelligence agent's next-open forecast:

* ``load_mvp_spec()`` must return a canonical, immutable :class:`MVPSpec`
  with a stable set of required input and output fields plus a non-empty
  ordered list of :class:`Requirement` entries.
* ``validate_forecast_shape(payload)`` must accept any dict matching the
  spec's ``required_outputs`` and reject non-dicts, missing fields, and
  empty required values with :class:`RequirementsError`.

TDD history
-----------
PRODMARKET-3 introduced these tests marked ``xfail(strict=True, ...)`` so
CI stayed green while the implementation ticket (PRODMARKET-4) was open.
PRODMARKET-4 delivers the implementation and removes the ``xfail`` markers
so the behaviour tests now assert real behaviour on every run.

External deps
-------------
None. Everything is exercised in-process — the module has no I/O and no
network calls, so no mocking is needed.
"""
from __future__ import annotations

import dataclasses

import pytest

from market_intel.mvp_requirements import (
    MVPSpec,
    Requirement,
    RequirementsError,
    load_mvp_spec,
    validate_forecast_shape,
)

# ---------------------------------------------------------------------------
# Dataclass shape — locks the public contract
# ---------------------------------------------------------------------------


def test_requirement_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(Requirement)}
    assert field_names == {"id", "title", "description", "category"}
    assert Requirement.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_mvpspec_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(MVPSpec)}
    assert field_names == {"required_inputs", "required_outputs", "requirements"}
    assert MVPSpec.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_requirements_error_is_valueerror_subclass():
    # Callers can catch the broad ValueError family without importing our
    # module — pin this so future refactors don't break that contract.
    assert issubclass(RequirementsError, ValueError)


# ---------------------------------------------------------------------------
# load_mvp_spec — happy path
# ---------------------------------------------------------------------------


def test_load_mvp_spec_returns_mvpspec_instance():
    spec = load_mvp_spec()
    assert isinstance(spec, MVPSpec)


def test_load_mvp_spec_declares_required_input_contract():
    spec = load_mvp_spec()
    expected = {"symbol", "timestamp", "open", "close", "volume"}
    assert expected.issubset(set(spec.required_inputs)), (
        f"required_inputs must cover {expected}, got {spec.required_inputs}"
    )


def test_load_mvp_spec_declares_required_output_contract():
    spec = load_mvp_spec()
    expected = {
        "symbol",
        "predicted_open",
        "forecast_for",
        "confidence",
        "generated_at",
    }
    assert expected.issubset(set(spec.required_outputs)), (
        f"required_outputs must cover {expected}, got {spec.required_outputs}"
    )


def test_load_mvp_spec_has_non_empty_ordered_requirements():
    spec = load_mvp_spec()
    assert isinstance(spec.requirements, tuple)
    assert len(spec.requirements) >= 1
    assert all(isinstance(r, Requirement) for r in spec.requirements)


def test_load_mvp_spec_requirement_ids_are_unique_and_non_empty():
    spec = load_mvp_spec()
    ids = [r.id for r in spec.requirements]
    assert all(rid for rid in ids), "requirement ids must be non-empty"
    assert len(ids) == len(set(ids)), f"requirement ids must be unique, got {ids}"


def test_load_mvp_spec_requirement_categories_are_from_allowed_set():
    spec = load_mvp_spec()
    allowed = {"input", "output", "behaviour", "operability"}
    bad = [r for r in spec.requirements if r.category not in allowed]
    assert not bad, f"requirements with disallowed category: {bad}"


# ---------------------------------------------------------------------------
# load_mvp_spec — determinism (CI must see the same spec every run)
# ---------------------------------------------------------------------------


def test_load_mvp_spec_is_deterministic_across_calls():
    assert load_mvp_spec() == load_mvp_spec()


# ---------------------------------------------------------------------------
# validate_forecast_shape — happy paths
# ---------------------------------------------------------------------------


def _valid_payload(spec: MVPSpec) -> dict[str, object]:
    return {name: f"value-{name}" for name in spec.required_outputs}


def test_validate_forecast_shape_accepts_payload_with_all_required_fields():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    validate_forecast_shape(payload)  # must not raise


def test_validate_forecast_shape_accepts_payload_with_extra_fields():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload["debug_note"] = "extra field is fine"
    validate_forecast_shape(payload)


# ---------------------------------------------------------------------------
# validate_forecast_shape — edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "forecast", 42, 3.14, ("symbol", "predicted_open")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_validate_forecast_shape_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(RequirementsError):
        validate_forecast_shape(not_a_dict)  # type: ignore[arg-type]


def test_validate_forecast_shape_rejects_missing_required_field():
    spec = load_mvp_spec()
    assert spec.required_outputs, "spec must have at least one required output"
    missing = spec.required_outputs[0]
    payload = _valid_payload(spec)
    del payload[missing]

    with pytest.raises(RequirementsError) as exc_info:
        validate_forecast_shape(payload)
    assert missing in str(exc_info.value)


def test_validate_forecast_shape_rejects_empty_required_value():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload[spec.required_outputs[0]] = ""

    with pytest.raises(RequirementsError):
        validate_forecast_shape(payload)


def test_validate_forecast_shape_rejects_none_required_value():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload[spec.required_outputs[0]] = None

    with pytest.raises(RequirementsError):
        validate_forecast_shape(payload)


# ---------------------------------------------------------------------------
# validate_forecast_shape — additional edge / failure-path coverage
# ---------------------------------------------------------------------------


def test_validate_forecast_shape_rejects_all_fields_missing():
    with pytest.raises(RequirementsError) as exc_info:
        validate_forecast_shape({})
    msg = str(exc_info.value)
    for field in load_mvp_spec().required_outputs:
        assert field in msg


def test_validate_forecast_shape_accepts_non_string_non_empty_values():
    # Numeric and structured values are legitimate for fields like
    # ``predicted_open`` and ``confidence`` — only empty strings and None
    # are treated as empty.
    spec = load_mvp_spec()
    payload: dict[str, object] = _valid_payload(spec)
    payload["predicted_open"] = 187.42
    payload["confidence"] = 0.0  # a zero confidence is still a real value
    payload["symbol"] = "AAPL"
    validate_forecast_shape(payload)


# ---------------------------------------------------------------------------
# Immutability of the canonical spec (frozen dataclass guarantees)
# ---------------------------------------------------------------------------


def test_requirement_instance_is_immutable():
    req = Requirement(id="X", title="t", description="d", category="input")
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.title = "changed"  # type: ignore[misc]


def test_mvpspec_instance_is_immutable():
    spec = load_mvp_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.required_inputs = ()  # type: ignore[misc]


def test_mvpspec_field_containers_are_tuples():
    # Tuples are immutable, so downstream callers cannot mutate the canonical
    # spec accidentally.
    spec = load_mvp_spec()
    assert isinstance(spec.required_inputs, tuple)
    assert isinstance(spec.required_outputs, tuple)
    assert isinstance(spec.requirements, tuple)


def test_requirement_is_hashable():
    # Frozen dataclasses should be hashable so callers can store them in sets
    # or use them as dict keys.
    req = Requirement(id="X", title="t", description="d", category="input")
    assert hash(req) == hash(req)
    assert {req} == {req}


# ---------------------------------------------------------------------------
# Canonical requirement content — MVP-R1..MVP-R4 with category coverage
# ---------------------------------------------------------------------------


def test_load_mvp_spec_contains_canonical_requirement_ids():
    spec = load_mvp_spec()
    ids = {r.id for r in spec.requirements}
    assert {"MVP-R1", "MVP-R2", "MVP-R3", "MVP-R4"}.issubset(ids)


def test_load_mvp_spec_covers_all_allowed_categories():
    spec = load_mvp_spec()
    categories = {r.category for r in spec.requirements}
    assert categories == {"input", "output", "behaviour", "operability"}


def test_load_mvp_spec_requirement_titles_and_descriptions_are_non_empty():
    spec = load_mvp_spec()
    for r in spec.requirements:
        assert r.title.strip(), f"requirement {r.id} has empty title"
        assert r.description.strip(), f"requirement {r.id} has empty description"


def test_mvp_r3_addresses_market_movement_insights_for_analysts():
    # PRODMARKET-4 explicitly ships MVP-R3 for delivering detailed
    # market-movement insights to financial analysts — pin the intent so a
    # future refactor cannot silently drop it.
    spec = load_mvp_spec()
    r3 = next((r for r in spec.requirements if r.id == "MVP-R3"), None)
    assert r3 is not None, "MVP-R3 must be present in the canonical spec"
    assert r3.category == "behaviour"
    text = (r3.title + " " + r3.description).lower()
    assert any(kw in text for kw in ("market", "insight", "driver", "move"))


# ---------------------------------------------------------------------------
# load_mvp_spec — determinism across independent instances
# ---------------------------------------------------------------------------


def test_load_mvp_spec_repeated_calls_have_equal_requirements():
    a = load_mvp_spec()
    b = load_mvp_spec()
    assert a.requirements == b.requirements
    assert a.required_inputs == b.required_inputs
    assert a.required_outputs == b.required_outputs


# ---------------------------------------------------------------------------
# validate_forecast_shape — error message aggregates all offending fields
# ---------------------------------------------------------------------------


def test_validate_forecast_shape_reports_multiple_missing_fields():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    dropped = list(spec.required_outputs[:2])
    for f in dropped:
        del payload[f]

    with pytest.raises(RequirementsError) as exc_info:
        validate_forecast_shape(payload)
    msg = str(exc_info.value)
    for f in dropped:
        assert f in msg


def test_validate_forecast_shape_reports_multiple_empty_fields():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload[spec.required_outputs[0]] = ""
    payload[spec.required_outputs[1]] = None

    with pytest.raises(RequirementsError) as exc_info:
        validate_forecast_shape(payload)
    msg = str(exc_info.value)
    assert spec.required_outputs[0] in msg
    assert spec.required_outputs[1] in msg


def test_validate_forecast_shape_non_dict_error_names_actual_type():
    with pytest.raises(RequirementsError) as exc_info:
        validate_forecast_shape("not a dict")  # type: ignore[arg-type]
    assert "str" in str(exc_info.value)


def test_validate_forecast_shape_accepts_whitespace_string_values():
    # A whitespace-only string is not an empty string — the contract only
    # rejects None and the literal empty string. Pin this so a future
    # refactor doesn't silently tighten the rule and break callers.
    spec = load_mvp_spec()
    payload: dict[str, object] = _valid_payload(spec)
    payload[spec.required_outputs[0]] = " "
    validate_forecast_shape(payload)


def test_validate_forecast_shape_accepts_zero_and_false_values():
    # ``0``, ``0.0``, and ``False`` are legitimate non-empty values — the
    # contract only rejects None and the literal empty string.
    spec = load_mvp_spec()
    payload: dict[str, object] = _valid_payload(spec)
    payload["confidence"] = 0
    payload["predicted_open"] = 0.0
    payload["generated_at"] = False
    validate_forecast_shape(payload)


def test_validate_forecast_shape_does_not_mutate_payload():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    snapshot = dict(payload)
    validate_forecast_shape(payload)
    assert payload == snapshot


# ---------------------------------------------------------------------------
# Module surface — __all__ pins the public API
# ---------------------------------------------------------------------------


def test_module_exports_expected_public_symbols():
    from market_intel import mvp_requirements

    assert set(mvp_requirements.__all__) == {
        "MVPSpec",
        "Requirement",
        "RequirementsError",
        "load_mvp_spec",
        "validate_forecast_shape",
    }
