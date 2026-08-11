"""Tests for the Production Release Requirements contract.

Test intent
-----------
These tests describe the *shape* the Production Release Requirements contract
must satisfy for the market-intelligence agent's production deployment gate:

* ``load_production_release_spec()`` must return a canonical, immutable
  :class:`ProductionReleaseSpec` with a stable set of required readiness fields
  and a non-empty ordered list of :class:`ReleaseRequirement` entries spanning
  quality, performance, security, and operability categories.
* ``validate_release_readiness(payload)`` must accept any dict matching the
  spec's ``required_readiness_fields`` and reject non-dicts, missing fields,
  and empty required values with :class:`ReleaseRequirementsError`.

TDD history
-----------
PRODMARKET-7 introduced these tests marked ``xfail(strict=True, ...)`` so
CI stays green while the implementation ticket (PRODMARKET-8) is open.
PRODMARKET-8 will deliver the implementation and remove the ``xfail`` markers
so the behaviour tests assert real behaviour on every run.

External deps
-------------
None. Everything is exercised in-process — the module has no I/O and no
network calls, so no mocking is needed.
"""
from __future__ import annotations

import dataclasses

import pytest

from market_intel.production_release_requirements import (
    ProductionReleaseSpec,
    ReleaseRequirement,
    ReleaseRequirementsError,
    load_production_release_spec,
    validate_release_readiness,
)

# ---------------------------------------------------------------------------
# Dataclass shape — locks the public contract (these pass today)
# ---------------------------------------------------------------------------


def test_release_requirement_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(ReleaseRequirement)}
    assert field_names == {"id", "title", "description", "category"}
    assert ReleaseRequirement.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_production_release_spec_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(ProductionReleaseSpec)}
    assert field_names == {"required_readiness_fields", "requirements"}
    assert ProductionReleaseSpec.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_release_requirements_error_is_valueerror_subclass():
    assert issubclass(ReleaseRequirementsError, ValueError)


def test_release_requirement_instance_is_immutable():
    req = ReleaseRequirement(id="X", title="t", description="d", category="quality")
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.title = "changed"  # type: ignore[misc]


def test_release_requirement_is_hashable():
    req = ReleaseRequirement(id="X", title="t", description="d", category="quality")
    assert hash(req) == hash(req)
    assert {req} == {req}


def test_module_exports_expected_public_symbols():
    from market_intel import production_release_requirements

    assert set(production_release_requirements.__all__) == {
        "ProductionReleaseSpec",
        "ReleaseRequirement",
        "ReleaseRequirementsError",
        "load_production_release_spec",
        "validate_release_readiness",
    }


# ---------------------------------------------------------------------------
# load_production_release_spec — behaviour tests (xfail until PRODMARKET-8)
# ---------------------------------------------------------------------------

_XFAIL = pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="Pending ProductionReleaseSpec implementation (PRODMARKET-8)",
)


@_XFAIL
def test_load_production_release_spec_returns_spec_instance():
    spec = load_production_release_spec()
    assert isinstance(spec, ProductionReleaseSpec)


@_XFAIL
def test_load_production_release_spec_declares_required_readiness_fields():
    spec = load_production_release_spec()
    expected = {
        "release_id",
        "test_coverage_pct",
        "security_scan_passed",
        "performance_benchmark_passed",
        "approved_by",
    }
    assert expected.issubset(set(spec.required_readiness_fields)), (
        f"required_readiness_fields must cover {expected}, "
        f"got {spec.required_readiness_fields}"
    )


@_XFAIL
def test_load_production_release_spec_has_non_empty_ordered_requirements():
    spec = load_production_release_spec()
    assert isinstance(spec.requirements, tuple)
    assert len(spec.requirements) >= 1
    assert all(isinstance(r, ReleaseRequirement) for r in spec.requirements)


@_XFAIL
def test_load_production_release_spec_requirement_ids_are_unique_and_non_empty():
    spec = load_production_release_spec()
    ids = [r.id for r in spec.requirements]
    assert all(rid for rid in ids), "requirement ids must be non-empty"
    assert len(ids) == len(set(ids)), f"requirement ids must be unique, got {ids}"


@_XFAIL
def test_load_production_release_spec_categories_are_from_allowed_set():
    spec = load_production_release_spec()
    allowed = {"quality", "performance", "security", "operability"}
    bad = [r for r in spec.requirements if r.category not in allowed]
    assert not bad, f"requirements with disallowed category: {bad}"


@_XFAIL
def test_load_production_release_spec_covers_all_allowed_categories():
    spec = load_production_release_spec()
    categories = {r.category for r in spec.requirements}
    assert categories == {"quality", "performance", "security", "operability"}


@_XFAIL
def test_load_production_release_spec_requirement_titles_and_descriptions_non_empty():
    spec = load_production_release_spec()
    for r in spec.requirements:
        assert r.title.strip(), f"requirement {r.id} has empty title"
        assert r.description.strip(), f"requirement {r.id} has empty description"


@_XFAIL
def test_load_production_release_spec_is_deterministic_across_calls():
    assert load_production_release_spec() == load_production_release_spec()


@_XFAIL
def test_load_production_release_spec_repeated_calls_have_equal_requirements():
    a = load_production_release_spec()
    b = load_production_release_spec()
    assert a.requirements == b.requirements
    assert a.required_readiness_fields == b.required_readiness_fields


@_XFAIL
def test_load_production_release_spec_field_containers_are_tuples():
    spec = load_production_release_spec()
    assert isinstance(spec.required_readiness_fields, tuple)
    assert isinstance(spec.requirements, tuple)


@_XFAIL
def test_production_release_spec_instance_is_immutable():
    spec = load_production_release_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.required_readiness_fields = ()  # type: ignore[misc]


@_XFAIL
def test_load_production_release_spec_contains_canonical_requirement_ids():
    spec = load_production_release_spec()
    ids = {r.id for r in spec.requirements}
    assert {"PRR-R1", "PRR-R2", "PRR-R3", "PRR-R4"}.issubset(ids)


@_XFAIL
def test_load_production_release_spec_has_quality_gate_requirement():
    spec = load_production_release_spec()
    quality_reqs = [r for r in spec.requirements if r.category == "quality"]
    assert quality_reqs, "spec must include at least one quality gate requirement"
    text = " ".join((r.title + " " + r.description).lower() for r in quality_reqs)
    assert any(kw in text for kw in ("test", "coverage", "review", "quality"))


@_XFAIL
def test_load_production_release_spec_has_security_gate_requirement():
    spec = load_production_release_spec()
    security_reqs = [r for r in spec.requirements if r.category == "security"]
    assert security_reqs, "spec must include at least one security gate requirement"
    text = " ".join((r.title + " " + r.description).lower() for r in security_reqs)
    assert any(kw in text for kw in ("security", "scan", "vulnerabilit", "secret"))


@_XFAIL
def test_load_production_release_spec_has_performance_gate_requirement():
    spec = load_production_release_spec()
    perf_reqs = [r for r in spec.requirements if r.category == "performance"]
    assert perf_reqs, "spec must include at least one performance gate requirement"
    text = " ".join((r.title + " " + r.description).lower() for r in perf_reqs)
    assert any(kw in text for kw in ("latency", "throughput", "benchmark", "performance"))


@_XFAIL
def test_load_production_release_spec_has_operability_gate_requirement():
    spec = load_production_release_spec()
    ops_reqs = [r for r in spec.requirements if r.category == "operability"]
    assert ops_reqs, "spec must include at least one operability gate requirement"
    text = " ".join((r.title + " " + r.description).lower() for r in ops_reqs)
    assert any(kw in text for kw in ("monitor", "alert", "rollback", "observ", "deploy"))


# ---------------------------------------------------------------------------
# validate_release_readiness — behaviour tests (xfail until PRODMARKET-8)
# ---------------------------------------------------------------------------


def _valid_readiness_payload(spec: ProductionReleaseSpec) -> dict[str, object]:
    return {name: f"value-{name}" for name in spec.required_readiness_fields}


@_XFAIL
def test_validate_release_readiness_accepts_payload_with_all_required_fields():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    validate_release_readiness(payload)  # must not raise


@_XFAIL
def test_validate_release_readiness_accepts_payload_with_extra_fields():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload["debug_note"] = "extra field is fine"
    validate_release_readiness(payload)


@_XFAIL
@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "release", 42, 3.14, ("release_id", "approved_by")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_validate_release_readiness_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(ReleaseRequirementsError):
        validate_release_readiness(not_a_dict)  # type: ignore[arg-type]


@_XFAIL
def test_validate_release_readiness_non_dict_error_names_actual_type():
    with pytest.raises(ReleaseRequirementsError) as exc_info:
        validate_release_readiness("not a dict")  # type: ignore[arg-type]
    assert "str" in str(exc_info.value)


@_XFAIL
def test_validate_release_readiness_rejects_missing_required_field():
    spec = load_production_release_spec()
    assert spec.required_readiness_fields, "spec must have at least one required field"
    missing = spec.required_readiness_fields[0]
    payload = _valid_readiness_payload(spec)
    del payload[missing]

    with pytest.raises(ReleaseRequirementsError) as exc_info:
        validate_release_readiness(payload)
    assert missing in str(exc_info.value)


@_XFAIL
def test_validate_release_readiness_rejects_empty_required_value():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload[spec.required_readiness_fields[0]] = ""

    with pytest.raises(ReleaseRequirementsError):
        validate_release_readiness(payload)


@_XFAIL
def test_validate_release_readiness_rejects_none_required_value():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload[spec.required_readiness_fields[0]] = None

    with pytest.raises(ReleaseRequirementsError):
        validate_release_readiness(payload)


@_XFAIL
def test_validate_release_readiness_rejects_all_fields_missing():
    with pytest.raises(ReleaseRequirementsError) as exc_info:
        validate_release_readiness({})
    msg = str(exc_info.value)
    for field in load_production_release_spec().required_readiness_fields:
        assert field in msg


@_XFAIL
def test_validate_release_readiness_reports_multiple_missing_fields():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    dropped = list(spec.required_readiness_fields[:2])
    for f in dropped:
        del payload[f]

    with pytest.raises(ReleaseRequirementsError) as exc_info:
        validate_release_readiness(payload)
    msg = str(exc_info.value)
    for f in dropped:
        assert f in msg


@_XFAIL
def test_validate_release_readiness_reports_multiple_empty_fields():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload[spec.required_readiness_fields[0]] = ""
    payload[spec.required_readiness_fields[1]] = None

    with pytest.raises(ReleaseRequirementsError) as exc_info:
        validate_release_readiness(payload)
    msg = str(exc_info.value)
    assert spec.required_readiness_fields[0] in msg
    assert spec.required_readiness_fields[1] in msg


@_XFAIL
def test_validate_release_readiness_accepts_non_string_non_empty_values():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload["test_coverage_pct"] = 95.3
    payload["performance_benchmark_passed"] = True
    validate_release_readiness(payload)


@_XFAIL
def test_validate_release_readiness_accepts_whitespace_string_values():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload[spec.required_readiness_fields[0]] = " "
    validate_release_readiness(payload)


@_XFAIL
def test_validate_release_readiness_accepts_zero_and_false_values():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    payload["test_coverage_pct"] = 0
    payload["performance_benchmark_passed"] = False
    validate_release_readiness(payload)


@_XFAIL
def test_validate_release_readiness_does_not_mutate_payload():
    spec = load_production_release_spec()
    payload = _valid_readiness_payload(spec)
    snapshot = dict(payload)
    try:
        validate_release_readiness(payload)
    except (ReleaseRequirementsError, NotImplementedError):
        pass
    assert payload == snapshot


# ---------------------------------------------------------------------------
# Additional contract tests added by PRODMARKET-7 tester
# ---------------------------------------------------------------------------


def test_release_requirement_equality_between_equal_instances():
    a = ReleaseRequirement(id="P1", title="t", description="d", category="quality")
    b = ReleaseRequirement(id="P1", title="t", description="d", category="quality")
    assert a == b


def test_release_requirement_inequality_between_different_instances():
    a = ReleaseRequirement(id="P1", title="t", description="d", category="quality")
    b = ReleaseRequirement(id="P2", title="t", description="d", category="quality")
    assert a != b


def test_release_requirements_error_carries_message():
    msg = "missing field: release_id"
    err = ReleaseRequirementsError(msg)
    assert str(err) == msg


def test_release_requirements_error_is_catchable_as_valueerror():
    with pytest.raises(ValueError):
        raise ReleaseRequirementsError("bad payload")


def test_load_production_release_spec_raises_not_implemented_error():
    with pytest.raises(NotImplementedError):
        load_production_release_spec()


def test_load_production_release_spec_not_implemented_message_references_prodmarket_8():
    with pytest.raises(NotImplementedError, match="PRODMARKET-8"):
        load_production_release_spec()


def test_validate_release_readiness_raises_not_implemented_error():
    with pytest.raises(NotImplementedError):
        validate_release_readiness({})


def test_validate_release_readiness_not_implemented_message_references_prodmarket_8():
    with pytest.raises(NotImplementedError, match="PRODMARKET-8"):
        validate_release_readiness({})
