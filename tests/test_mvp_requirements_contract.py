"""Supplementary contract tests for :mod:`market_intel.mvp_requirements`.

These tests complement ``tests/test_mvp_requirements.py`` (PRODMARKET-3) by
locking additional invariants of the public contract that hold independent
of whether the behaviour-level stubs have been implemented yet:

* frozen dataclass semantics (immutability + hashability + equality)
* public API surface exposed by ``__all__``
* ``RequirementsError`` accepts and preserves messages
* stub functions currently raise ``NotImplementedError`` — the "guardrail"
  tests use ``xfail(strict=True, raises=NotImplementedError)`` so that once
  the implementation ticket (PRODMARKET-4) lands, the XPASS forces removal
  of the stale marker (mirroring the pattern used by the developer's tests).

No external dependencies: the module is pure Python with no I/O, so no
mocks are required.
"""
from __future__ import annotations

import dataclasses

import pytest

import market_intel.mvp_requirements as mvp_mod
from market_intel.mvp_requirements import (
    MVPSpec,
    Requirement,
    RequirementsError,
    load_mvp_spec,
    validate_forecast_shape,
)


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------


def test_module_all_exposes_expected_public_names():
    expected = {
        "MVPSpec",
        "Requirement",
        "RequirementsError",
        "load_mvp_spec",
        "validate_forecast_shape",
    }
    assert set(mvp_mod.__all__) == expected


@pytest.mark.parametrize(
    "name",
    ["MVPSpec", "Requirement", "RequirementsError", "load_mvp_spec", "validate_forecast_shape"],
)
def test_public_names_are_importable_from_module(name):
    assert hasattr(mvp_mod, name), f"expected {name} to be exported from mvp_requirements"


# ---------------------------------------------------------------------------
# Requirement dataclass — immutability, equality, hashability
# ---------------------------------------------------------------------------


def _sample_requirement(**overrides) -> Requirement:
    kwargs = {
        "id": "MVP-R1",
        "title": "Accept OHLCV rows",
        "description": "The agent must accept OHLCV rows as input.",
        "category": "input",
    }
    kwargs.update(overrides)
    return Requirement(**kwargs)


def test_requirement_instances_are_immutable():
    req = _sample_requirement()
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.id = "MVP-R99"  # type: ignore[misc]


def test_requirement_equality_is_by_value():
    a = _sample_requirement()
    b = _sample_requirement()
    assert a == b
    assert a is not b


def test_requirement_differs_when_any_field_differs():
    base = _sample_requirement()
    assert base != _sample_requirement(id="MVP-R2")
    assert base != _sample_requirement(title="Other title")
    assert base != _sample_requirement(description="Other description")
    assert base != _sample_requirement(category="output")


def test_requirement_is_hashable_due_to_frozen():
    a = _sample_requirement()
    b = _sample_requirement()
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


# ---------------------------------------------------------------------------
# MVPSpec dataclass — immutability, equality, hashability
# ---------------------------------------------------------------------------


def _sample_spec(**overrides) -> MVPSpec:
    kwargs = {
        "required_inputs": ("symbol", "timestamp", "open", "close", "volume"),
        "required_outputs": (
            "symbol",
            "predicted_open",
            "forecast_for",
            "confidence",
            "generated_at",
        ),
        "requirements": (_sample_requirement(),),
    }
    kwargs.update(overrides)
    return MVPSpec(**kwargs)


def test_mvpspec_instances_are_immutable():
    spec = _sample_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.required_inputs = ("x",)  # type: ignore[misc]


def test_mvpspec_equality_is_by_value():
    a = _sample_spec()
    b = _sample_spec()
    assert a == b
    assert a is not b


def test_mvpspec_is_hashable_when_fields_are_hashable():
    a = _sample_spec()
    b = _sample_spec()
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


def test_mvpspec_field_types_declared_as_tuples():
    spec = _sample_spec()
    assert isinstance(spec.required_inputs, tuple)
    assert isinstance(spec.required_outputs, tuple)
    assert isinstance(spec.requirements, tuple)


# ---------------------------------------------------------------------------
# RequirementsError — message preservation and catchability
# ---------------------------------------------------------------------------


def test_requirements_error_preserves_message():
    err = RequirementsError("missing field: symbol")
    assert "missing field: symbol" in str(err)


def test_requirements_error_can_be_caught_as_valueerror():
    with pytest.raises(ValueError):
        raise RequirementsError("boom")


def test_requirements_error_can_be_raised_without_args():
    err = RequirementsError()
    assert isinstance(err, ValueError)


# ---------------------------------------------------------------------------
# Stub guardrails — currently raise NotImplementedError
# ---------------------------------------------------------------------------

_PENDING = pytest.mark.xfail(
    strict=True,
    reason="Pending PRODMARKET-4 implementation of load_mvp_spec / validate_forecast_shape",
    raises=NotImplementedError,
)


@_PENDING
def test_load_mvp_spec_stub_raises_not_implemented():
    load_mvp_spec()


@_PENDING
def test_validate_forecast_shape_stub_raises_not_implemented():
    validate_forecast_shape({})


# ---------------------------------------------------------------------------
# Callable signatures — sanity-check that the stubs remain callable
# ---------------------------------------------------------------------------


def test_load_mvp_spec_is_callable():
    assert callable(load_mvp_spec)


def test_validate_forecast_shape_is_callable():
    assert callable(validate_forecast_shape)
