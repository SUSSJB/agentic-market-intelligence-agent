"""Tests for the Acceptance Test Plan (ATP) contract.

Test intent
-----------
These tests describe the *shape* the Acceptance Test Plan must satisfy for
the market-intelligence agent's next-open forecast:

* ``load_acceptance_test_plan()`` must return a canonical, immutable
  :class:`AcceptanceTestPlan` with a non-empty ordered tuple of
  :class:`AcceptanceCase` entries and a stable ``required_result_fields``
  contract for test-result payloads.
* Every canonical case must cover at least one MVP requirement id
  (``MVP-R1..MVP-R4``) so the ATP is anchored to the MVP contract shipped
  under PRODMARKET-4.
* ``validate_test_result(payload)`` must accept any dict matching the
  plan's ``required_result_fields`` (with a ``case_id`` present in the
  plan and a ``status`` from the allowed set) and reject non-dicts,
  missing fields, empty required values, unknown ``case_id`` values, and
  ``status`` values outside the allowed set -- always with
  :class:`TestPlanError`.

TDD scaffolding convention
--------------------------
Behaviour tests below are marked
``xfail(strict=True, raises=NotImplementedError,
        reason="Pending Acceptance Test Plan implementation ticket")``
so CI stays deterministic (green) while the implementation is open. Once
the implementation makes any of them pass, ``strict=True`` flips it to
XPASS and turns CI red until the marker is removed -- forcing the
follow-up PR to actually delete the pending markers. This mirrors the
approach established in PRODMARKET-3 for the MVP Requirements contract
(see ``ARCHITECTURE.md``).

External deps
-------------
None. Everything is exercised in-process -- the module has no I/O and no
network calls, so no mocking is needed.
"""
from __future__ import annotations

import dataclasses

import pytest

from market_intel.acceptance_test_plan import (
    AcceptanceCase,
    AcceptanceTestPlan,
    TestPlanError,
    load_acceptance_test_plan,
    validate_test_result,
)


# ---------------------------------------------------------------------------
# Dataclass shape -- locks the public contract, passes today
# ---------------------------------------------------------------------------


def test_acceptance_case_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(AcceptanceCase)}
    assert field_names == {
        "id",
        "title",
        "given",
        "when",
        "then",
        "category",
        "covers",
    }
    assert AcceptanceCase.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_acceptance_test_plan_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(AcceptanceTestPlan)}
    assert field_names == {"cases", "required_result_fields"}
    assert AcceptanceTestPlan.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_test_plan_error_is_valueerror_subclass():
    # Callers can catch the broad ValueError family without importing our
    # module -- pin this so future refactors don't break that contract.
    assert issubclass(TestPlanError, ValueError)


def test_acceptance_case_instance_is_immutable():
    case = AcceptanceCase(
        id="ATP-C0",
        title="t",
        given="g",
        when="w",
        then="th",
        category="happy_path",
        covers=("MVP-R1",),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        case.title = "changed"  # type: ignore[misc]


def test_acceptance_case_is_hashable():
    # Frozen dataclasses should be hashable so callers can store them in sets.
    case = AcceptanceCase(
        id="ATP-C0",
        title="t",
        given="g",
        when="w",
        then="th",
        category="happy_path",
        covers=("MVP-R1",),
    )
    assert hash(case) == hash(case)
    assert {case} == {case}


def test_module_exports_expected_public_symbols():
    from market_intel import acceptance_test_plan

    assert set(acceptance_test_plan.__all__) == {
        "AcceptanceCase",
        "AcceptanceTestPlan",
        "TestPlanError",
        "load_acceptance_test_plan",
        "validate_test_result",
    }


# ---------------------------------------------------------------------------
# load_acceptance_test_plan -- behaviour tests, xfail until implementation
# ---------------------------------------------------------------------------


def test_load_acceptance_test_plan_returns_plan_instance():
    plan = load_acceptance_test_plan()
    assert isinstance(plan, AcceptanceTestPlan)


def test_load_acceptance_test_plan_has_non_empty_ordered_cases():
    plan = load_acceptance_test_plan()
    assert isinstance(plan.cases, tuple)
    assert len(plan.cases) >= 1
    assert all(isinstance(c, AcceptanceCase) for c in plan.cases)


def test_load_acceptance_test_plan_case_ids_are_unique_and_non_empty():
    plan = load_acceptance_test_plan()
    ids = [c.id for c in plan.cases]
    assert all(cid for cid in ids), "case ids must be non-empty"
    assert len(ids) == len(set(ids)), f"case ids must be unique, got {ids}"


def test_load_acceptance_test_plan_case_categories_are_from_allowed_set():
    plan = load_acceptance_test_plan()
    allowed = {"happy_path", "edge_case", "regression"}
    bad = [c for c in plan.cases if c.category not in allowed]
    assert not bad, f"cases with disallowed category: {bad}"


def test_load_acceptance_test_plan_covers_happy_path_and_edge_case_categories():
    # The acceptance criteria explicitly require critical happy-path AND
    # edge-case coverage -- pin both are present in the canonical plan.
    plan = load_acceptance_test_plan()
    categories = {c.category for c in plan.cases}
    assert "happy_path" in categories
    assert "edge_case" in categories


def test_load_acceptance_test_plan_case_gwt_fields_are_non_empty():
    plan = load_acceptance_test_plan()
    for c in plan.cases:
        assert c.title.strip(), f"case {c.id} has empty title"
        assert c.given.strip(), f"case {c.id} has empty given clause"
        assert c.when.strip(), f"case {c.id} has empty when clause"
        assert c.then.strip(), f"case {c.id} has empty then clause"


def test_load_acceptance_test_plan_cases_cover_mvp_requirements():
    plan = load_acceptance_test_plan()
    for c in plan.cases:
        assert isinstance(c.covers, tuple)
        assert len(c.covers) >= 1, f"case {c.id} must cover at least one MVP req"
        for rid in c.covers:
            assert rid.startswith("MVP-R"), (
                f"case {c.id} covers unknown requirement id '{rid}'"
            )


def test_load_acceptance_test_plan_covers_every_mvp_requirement():
    # The ATP must anchor to the MVP contract shipped under PRODMARKET-4:
    # every canonical MVP requirement id needs at least one case exercising it.
    from market_intel.mvp_requirements import load_mvp_spec

    plan = load_acceptance_test_plan()
    covered = {rid for c in plan.cases for rid in c.covers}
    mvp_ids = {r.id for r in load_mvp_spec().requirements}
    missing = mvp_ids - covered
    assert not missing, f"MVP requirements not covered by any case: {sorted(missing)}"


def test_load_acceptance_test_plan_required_result_fields_contract():
    plan = load_acceptance_test_plan()
    expected = {"case_id", "status", "executed_at", "evidence"}
    assert expected.issubset(set(plan.required_result_fields)), (
        f"required_result_fields must cover {expected}, "
        f"got {plan.required_result_fields}"
    )


def test_load_acceptance_test_plan_field_containers_are_tuples():
    plan = load_acceptance_test_plan()
    assert isinstance(plan.cases, tuple)
    assert isinstance(plan.required_result_fields, tuple)


def test_load_acceptance_test_plan_is_deterministic_across_calls():
    assert load_acceptance_test_plan() == load_acceptance_test_plan()


def test_load_acceptance_test_plan_repeated_calls_have_equal_cases():
    a = load_acceptance_test_plan()
    b = load_acceptance_test_plan()
    assert a.cases == b.cases
    assert a.required_result_fields == b.required_result_fields


def test_load_acceptance_test_plan_instance_is_immutable():
    plan = load_acceptance_test_plan()
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.cases = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# validate_test_result -- happy paths, xfail until implementation
# ---------------------------------------------------------------------------


def _valid_result(plan: AcceptanceTestPlan) -> dict[str, object]:
    return {
        "case_id": plan.cases[0].id,
        "status": "passed",
        "executed_at": "2026-08-11T00:00:00Z",
        "evidence": "pytest -k atp_c1 => passed",
    }


def test_validate_test_result_accepts_payload_with_all_required_fields():
    plan = load_acceptance_test_plan()
    validate_test_result(_valid_result(plan))  # must not raise


def test_validate_test_result_accepts_payload_with_extra_fields():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    payload["debug_note"] = "extra field is fine"
    validate_test_result(payload)


@pytest.mark.parametrize(
    "status",
    ["passed", "failed", "skipped"],
    ids=["passed", "failed", "skipped"],
)
def test_validate_test_result_accepts_every_allowed_status(status):
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    payload["status"] = status
    validate_test_result(payload)


def test_validate_test_result_does_not_mutate_payload():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    snapshot = dict(payload)
    validate_test_result(payload)
    assert payload == snapshot


# ---------------------------------------------------------------------------
# validate_test_result -- edge cases and failure paths, xfail until impl
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "result", 42, 3.14, ("case_id", "status")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_validate_test_result_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(TestPlanError):
        validate_test_result(not_a_dict)  # type: ignore[arg-type]


def test_validate_test_result_rejects_missing_required_field():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    missing = plan.required_result_fields[0]
    del payload[missing]

    with pytest.raises(TestPlanError) as exc_info:
        validate_test_result(payload)
    assert missing in str(exc_info.value)


def test_validate_test_result_rejects_all_fields_missing():
    with pytest.raises(TestPlanError) as exc_info:
        validate_test_result({})
    msg = str(exc_info.value)
    for field in load_acceptance_test_plan().required_result_fields:
        assert field in msg


def test_validate_test_result_rejects_empty_required_value():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    payload[plan.required_result_fields[0]] = ""

    with pytest.raises(TestPlanError):
        validate_test_result(payload)


def test_validate_test_result_rejects_none_required_value():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    payload[plan.required_result_fields[0]] = None

    with pytest.raises(TestPlanError):
        validate_test_result(payload)


def test_validate_test_result_rejects_unknown_case_id():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    known_ids = {c.id for c in plan.cases}
    unknown = "ATP-NOT-A-REAL-CASE"
    assert unknown not in known_ids
    payload["case_id"] = unknown

    with pytest.raises(TestPlanError) as exc_info:
        validate_test_result(payload)
    assert unknown in str(exc_info.value)


def test_validate_test_result_rejects_disallowed_status():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    payload["status"] = "flaky"  # not in {passed, failed, skipped}

    with pytest.raises(TestPlanError) as exc_info:
        validate_test_result(payload)
    assert "flaky" in str(exc_info.value) or "status" in str(exc_info.value).lower()


def test_validate_test_result_reports_multiple_missing_fields():
    plan = load_acceptance_test_plan()
    payload = _valid_result(plan)
    dropped = list(plan.required_result_fields[:2])
    for f in dropped:
        del payload[f]

    with pytest.raises(TestPlanError) as exc_info:
        validate_test_result(payload)
    msg = str(exc_info.value)
    for f in dropped:
        assert f in msg


def test_validate_test_result_non_dict_error_names_actual_type():
    with pytest.raises(TestPlanError) as exc_info:
        validate_test_result("not a dict")  # type: ignore[arg-type]
    assert "str" in str(exc_info.value)
