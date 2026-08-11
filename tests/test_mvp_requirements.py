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
