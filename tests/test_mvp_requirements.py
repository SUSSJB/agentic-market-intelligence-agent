"""Failing tests for the MVP Requirements contract (PRODMARKET-3).

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

TDD posture
-----------
Behaviour tests are marked ``xfail(strict=True, ...)`` because the stubs in
``market_intel.mvp_requirements`` raise ``NotImplementedError``. This keeps
the CI run deterministic (green) while the implementation ticket is open,
and — thanks to ``strict=True`` — the moment the implementation makes a
test pass, pytest will report an unexpected pass (XPASS) and turn the
suite red until that test's ``xfail`` marker is removed. That is the
mechanism that forces the follow-up PR to actually delete the markers
rather than silently leaving them in place.

The dataclass-shape tests are *not* xfailed: they lock the public contract
today and must pass immediately.

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

_PENDING = pytest.mark.xfail(
    strict=True,
    reason="Pending PRODMARKET-4 implementation of load_mvp_spec / validate_forecast_shape",
    raises=NotImplementedError,
)


# ---------------------------------------------------------------------------
# Dataclass shape — locks the public contract, must pass today
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
# load_mvp_spec — happy path (pending implementation)
# ---------------------------------------------------------------------------


@_PENDING
def test_load_mvp_spec_returns_mvpspec_instance():
    spec = load_mvp_spec()
    assert isinstance(spec, MVPSpec)


@_PENDING
def test_load_mvp_spec_declares_required_input_contract():
    spec = load_mvp_spec()
    expected = {"symbol", "timestamp", "open", "close", "volume"}
    assert expected.issubset(set(spec.required_inputs)), (
        f"required_inputs must cover {expected}, got {spec.required_inputs}"
    )


@_PENDING
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


@_PENDING
def test_load_mvp_spec_has_non_empty_ordered_requirements():
    spec = load_mvp_spec()
    assert isinstance(spec.requirements, tuple)
    assert len(spec.requirements) >= 1
    assert all(isinstance(r, Requirement) for r in spec.requirements)


@_PENDING
def test_load_mvp_spec_requirement_ids_are_unique_and_non_empty():
    spec = load_mvp_spec()
    ids = [r.id for r in spec.requirements]
    assert all(rid for rid in ids), "requirement ids must be non-empty"
    assert len(ids) == len(set(ids)), f"requirement ids must be unique, got {ids}"


@_PENDING
def test_load_mvp_spec_requirement_categories_are_from_allowed_set():
    spec = load_mvp_spec()
    allowed = {"input", "output", "behaviour", "operability"}
    bad = [r for r in spec.requirements if r.category not in allowed]
    assert not bad, f"requirements with disallowed category: {bad}"


# ---------------------------------------------------------------------------
# load_mvp_spec — determinism (CI must see the same spec every run)
# ---------------------------------------------------------------------------


@_PENDING
def test_load_mvp_spec_is_deterministic_across_calls():
    assert load_mvp_spec() == load_mvp_spec()


# ---------------------------------------------------------------------------
# validate_forecast_shape — happy paths (pending implementation)
# ---------------------------------------------------------------------------


def _valid_payload(spec: MVPSpec) -> dict[str, object]:
    return {name: f"value-{name}" for name in spec.required_outputs}


@_PENDING
def test_validate_forecast_shape_accepts_payload_with_all_required_fields():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    validate_forecast_shape(payload)  # must not raise


@_PENDING
def test_validate_forecast_shape_accepts_payload_with_extra_fields():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload["debug_note"] = "extra field is fine"
    validate_forecast_shape(payload)


# ---------------------------------------------------------------------------
# validate_forecast_shape — edge cases (pending implementation)
# ---------------------------------------------------------------------------


@_PENDING
@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "forecast", 42, 3.14, ("symbol", "predicted_open")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_validate_forecast_shape_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(RequirementsError):
        validate_forecast_shape(not_a_dict)  # type: ignore[arg-type]


@_PENDING
def test_validate_forecast_shape_rejects_missing_required_field():
    spec = load_mvp_spec()
    assert spec.required_outputs, "spec must have at least one required output"
    missing = spec.required_outputs[0]
    payload = _valid_payload(spec)
    del payload[missing]

    with pytest.raises(RequirementsError) as exc_info:
        validate_forecast_shape(payload)
    assert missing in str(exc_info.value)


@_PENDING
def test_validate_forecast_shape_rejects_empty_required_value():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload[spec.required_outputs[0]] = ""

    with pytest.raises(RequirementsError):
        validate_forecast_shape(payload)


@_PENDING
def test_validate_forecast_shape_rejects_none_required_value():
    spec = load_mvp_spec()
    payload = _valid_payload(spec)
    payload[spec.required_outputs[0]] = None

    with pytest.raises(RequirementsError):
        validate_forecast_shape(payload)
