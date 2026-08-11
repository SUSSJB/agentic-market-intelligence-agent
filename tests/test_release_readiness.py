"""Tests for E2E integration and release readiness -- PRODMARKET-15.

Test-first: all behaviour tests are authored before the implementation
exists. Structural tests (dataclass shape, module surface) pass immediately.
Behaviour tests that require a real implementation are guarded with
``pytest.mark.xfail(strict=True, raises=NotImplementedError)`` and will flip
to XPASS (turning CI red) once the implementation is in place.
"""
from __future__ import annotations

import pytest

from market_intel.release_readiness import (
    DeploymentGate,
    E2EFlow,
    E2EFlowResult,
    ReleaseReadinessError,
    ReleaseReadinessSpec,
    load_release_readiness_spec,
    validate_deployment_readiness,
    validate_e2e_flow_result,
)


# ---------------------------------------------------------------------------
# Structural / module-surface tests (pass immediately)
# ---------------------------------------------------------------------------


class TestModuleSurface:
    def test_dataclass_e2e_flow_fields(self) -> None:
        flow = E2EFlow(
            id="E2E-F1",
            title="Happy path",
            description="Full journey",
            flow_type="happy_path",
            services=("market_intel",),
        )
        assert flow.id == "E2E-F1"
        assert flow.title == "Happy path"
        assert flow.description == "Full journey"
        assert flow.flow_type == "happy_path"
        assert flow.services == ("market_intel",)

    def test_dataclass_e2e_flow_is_frozen(self) -> None:
        flow = E2EFlow(
            id="E2E-F1",
            title="t",
            description="d",
            flow_type="happy_path",
            services=(),
        )
        with pytest.raises((AttributeError, TypeError)):
            flow.id = "other"  # type: ignore[misc]

    def test_dataclass_e2e_flow_result_fields(self) -> None:
        result = E2EFlowResult(
            flow_id="E2E-F1",
            status="passed",
            executed_at="2026-08-11T00:00:00Z",
            evidence="All checks passed",
        )
        assert result.flow_id == "E2E-F1"
        assert result.status == "passed"
        assert result.executed_at == "2026-08-11T00:00:00Z"
        assert result.evidence == "All checks passed"

    def test_dataclass_e2e_flow_result_is_frozen(self) -> None:
        result = E2EFlowResult(
            flow_id="E2E-F1",
            status="passed",
            executed_at="2026-08-11T00:00:00Z",
            evidence="ok",
        )
        with pytest.raises((AttributeError, TypeError)):
            result.status = "failed"  # type: ignore[misc]

    def test_dataclass_deployment_gate_fields(self) -> None:
        gate = DeploymentGate(
            id="DG-1",
            title="Test Coverage",
            description="All tests must pass",
            category="quality",
        )
        assert gate.id == "DG-1"
        assert gate.title == "Test Coverage"
        assert gate.category == "quality"

    def test_dataclass_deployment_gate_is_frozen(self) -> None:
        gate = DeploymentGate(
            id="DG-1",
            title="t",
            description="d",
            category="quality",
        )
        with pytest.raises((AttributeError, TypeError)):
            gate.id = "other"  # type: ignore[misc]

    def test_dataclass_release_readiness_spec_fields(self) -> None:
        spec = ReleaseReadinessSpec(
            flows=(
                E2EFlow(
                    id="E2E-F1",
                    title="t",
                    description="d",
                    flow_type="happy_path",
                    services=(),
                ),
            ),
            deployment_gates=(
                DeploymentGate(id="DG-1", title="t", description="d", category="quality"),
            ),
            required_readiness_fields=("gate_id", "passed"),
            rollback_steps=("step1",),
        )
        assert len(spec.flows) == 1
        assert len(spec.deployment_gates) == 1
        assert "gate_id" in spec.required_readiness_fields
        assert "step1" in spec.rollback_steps

    def test_release_readiness_error_is_value_error(self) -> None:
        err = ReleaseReadinessError("test")
        assert isinstance(err, ValueError)

    def test_module_exports(self) -> None:
        import market_intel.release_readiness as m

        assert hasattr(m, "DeploymentGate")
        assert hasattr(m, "E2EFlow")
        assert hasattr(m, "E2EFlowResult")
        assert hasattr(m, "ReleaseReadinessError")
        assert hasattr(m, "ReleaseReadinessSpec")
        assert hasattr(m, "load_release_readiness_spec")
        assert hasattr(m, "validate_deployment_readiness")
        assert hasattr(m, "validate_e2e_flow_result")


# ---------------------------------------------------------------------------
# Behaviour tests
# ---------------------------------------------------------------------------


class TestLoadReleaseReadinessSpec:
    def test_returns_release_readiness_spec(self) -> None:
        spec = load_release_readiness_spec()
        assert isinstance(spec, ReleaseReadinessSpec)

    def test_is_deterministic(self) -> None:
        spec1 = load_release_readiness_spec()
        spec2 = load_release_readiness_spec()
        assert spec1 == spec2

    def test_has_flows(self) -> None:
        spec = load_release_readiness_spec()
        assert len(spec.flows) >= 1

    def test_has_happy_path_flow(self) -> None:
        spec = load_release_readiness_spec()
        flow_types = {f.flow_type for f in spec.flows}
        assert "happy_path" in flow_types

    def test_has_failure_path_flow(self) -> None:
        spec = load_release_readiness_spec()
        flow_types = {f.flow_type for f in spec.flows}
        assert "failure_path" in flow_types

    def test_all_flows_have_unique_ids(self) -> None:
        spec = load_release_readiness_spec()
        ids = [f.id for f in spec.flows]
        assert len(ids) == len(set(ids))

    def test_all_flows_have_non_empty_fields(self) -> None:
        spec = load_release_readiness_spec()
        for flow in spec.flows:
            assert flow.id
            assert flow.title
            assert flow.description
            assert flow.flow_type
            assert len(flow.services) >= 1

    def test_flow_types_are_allowed(self) -> None:
        spec = load_release_readiness_spec()
        allowed = {"happy_path", "failure_path", "resiliency", "billing"}
        for flow in spec.flows:
            assert flow.flow_type in allowed, (
                f"flow {flow.id} has unexpected flow_type {flow.flow_type!r}"
            )

    def test_has_deployment_gates(self) -> None:
        spec = load_release_readiness_spec()
        assert len(spec.deployment_gates) >= 1

    def test_deployment_gate_ids_are_unique(self) -> None:
        spec = load_release_readiness_spec()
        ids = [g.id for g in spec.deployment_gates]
        assert len(ids) == len(set(ids))

    def test_deployment_gates_have_non_empty_fields(self) -> None:
        spec = load_release_readiness_spec()
        for gate in spec.deployment_gates:
            assert gate.id
            assert gate.title
            assert gate.description
            assert gate.category

    def test_deployment_gate_categories_are_allowed(self) -> None:
        spec = load_release_readiness_spec()
        allowed = {"quality", "security", "operability", "performance"}
        for gate in spec.deployment_gates:
            assert gate.category in allowed

    def test_required_readiness_fields_non_empty(self) -> None:
        spec = load_release_readiness_spec()
        assert len(spec.required_readiness_fields) >= 2

    def test_rollback_steps_present(self) -> None:
        spec = load_release_readiness_spec()
        assert len(spec.rollback_steps) >= 1

    def test_covers_monitoring_gate(self) -> None:
        spec = load_release_readiness_spec()
        categories = {g.category for g in spec.deployment_gates}
        assert "operability" in categories

    def test_covers_security_gate(self) -> None:
        spec = load_release_readiness_spec()
        categories = {g.category for g in spec.deployment_gates}
        assert "security" in categories

    def test_spec_is_hashable(self) -> None:
        spec = load_release_readiness_spec()
        _ = hash(spec)


# ---------------------------------------------------------------------------
# validate_e2e_flow_result
# ---------------------------------------------------------------------------


class TestValidateE2EFlowResult:
    def _valid_payload(self) -> dict:
        spec = load_release_readiness_spec()
        return {
            "flow_id": spec.flows[0].id,
            "status": "passed",
            "executed_at": "2026-08-11T00:00:00Z",
            "evidence": "All service calls succeeded",
        }

    def test_valid_payload_does_not_raise(self) -> None:
        validate_e2e_flow_result(self._valid_payload())

    def test_non_dict_raises(self) -> None:
        with pytest.raises(ReleaseReadinessError, match="dict"):
            validate_e2e_flow_result("not-a-dict")  # type: ignore[arg-type]

    def test_missing_flow_id_raises(self) -> None:
        payload = self._valid_payload()
        del payload["flow_id"]
        with pytest.raises(ReleaseReadinessError, match="flow_id"):
            validate_e2e_flow_result(payload)

    def test_missing_status_raises(self) -> None:
        payload = self._valid_payload()
        del payload["status"]
        with pytest.raises(ReleaseReadinessError, match="status"):
            validate_e2e_flow_result(payload)

    def test_missing_executed_at_raises(self) -> None:
        payload = self._valid_payload()
        del payload["executed_at"]
        with pytest.raises(ReleaseReadinessError, match="executed_at"):
            validate_e2e_flow_result(payload)

    def test_missing_evidence_raises(self) -> None:
        payload = self._valid_payload()
        del payload["evidence"]
        with pytest.raises(ReleaseReadinessError, match="evidence"):
            validate_e2e_flow_result(payload)

    def test_empty_flow_id_raises(self) -> None:
        payload = self._valid_payload()
        payload["flow_id"] = ""
        with pytest.raises(ReleaseReadinessError):
            validate_e2e_flow_result(payload)

    def test_none_evidence_raises(self) -> None:
        payload = self._valid_payload()
        payload["evidence"] = None
        with pytest.raises(ReleaseReadinessError):
            validate_e2e_flow_result(payload)

    def test_unknown_flow_id_raises(self) -> None:
        payload = self._valid_payload()
        payload["flow_id"] = "E2E-UNKNOWN-999"
        with pytest.raises(ReleaseReadinessError, match="E2E-UNKNOWN-999"):
            validate_e2e_flow_result(payload)

    def test_invalid_status_raises(self) -> None:
        payload = self._valid_payload()
        payload["status"] = "broken"
        with pytest.raises(ReleaseReadinessError, match="broken"):
            validate_e2e_flow_result(payload)

    def test_failed_status_is_accepted(self) -> None:
        payload = self._valid_payload()
        payload["status"] = "failed"
        validate_e2e_flow_result(payload)

    def test_skipped_status_is_accepted(self) -> None:
        payload = self._valid_payload()
        payload["status"] = "skipped"
        validate_e2e_flow_result(payload)

    def test_extra_fields_are_permitted(self) -> None:
        payload = self._valid_payload()
        payload["debug_trace"] = "extra metadata"
        validate_e2e_flow_result(payload)

    def test_payload_is_not_mutated(self) -> None:
        payload = self._valid_payload()
        original = dict(payload)
        validate_e2e_flow_result(payload)
        assert payload == original


# ---------------------------------------------------------------------------
# validate_deployment_readiness
# ---------------------------------------------------------------------------


class TestValidateDeploymentReadiness:
    def _valid_payload(self) -> dict:
        spec = load_release_readiness_spec()
        return {field: "verified" for field in spec.required_readiness_fields}

    def test_valid_payload_does_not_raise(self) -> None:
        validate_deployment_readiness(self._valid_payload())

    def test_non_dict_raises(self) -> None:
        with pytest.raises(ReleaseReadinessError, match="dict"):
            validate_deployment_readiness(42)  # type: ignore[arg-type]

    def test_missing_required_field_raises(self) -> None:
        spec = load_release_readiness_spec()
        payload = self._valid_payload()
        first_field = spec.required_readiness_fields[0]
        del payload[first_field]
        with pytest.raises(ReleaseReadinessError, match=first_field):
            validate_deployment_readiness(payload)

    def test_all_missing_fields_are_named(self) -> None:
        with pytest.raises(ReleaseReadinessError) as exc_info:
            validate_deployment_readiness({})
        spec = load_release_readiness_spec()
        error_msg = str(exc_info.value)
        for field in spec.required_readiness_fields:
            assert field in error_msg

    def test_none_value_raises(self) -> None:
        spec = load_release_readiness_spec()
        payload = self._valid_payload()
        payload[spec.required_readiness_fields[0]] = None
        with pytest.raises(ReleaseReadinessError):
            validate_deployment_readiness(payload)

    def test_empty_string_raises(self) -> None:
        spec = load_release_readiness_spec()
        payload = self._valid_payload()
        payload[spec.required_readiness_fields[0]] = ""
        with pytest.raises(ReleaseReadinessError):
            validate_deployment_readiness(payload)

    def test_extra_fields_are_permitted(self) -> None:
        payload = self._valid_payload()
        payload["extra"] = "data"
        validate_deployment_readiness(payload)

    def test_payload_is_not_mutated(self) -> None:
        payload = self._valid_payload()
        original = dict(payload)
        validate_deployment_readiness(payload)
        assert payload == original


# ---------------------------------------------------------------------------
# Cross-module integration: E2E happy-path smoke test
# ---------------------------------------------------------------------------


class TestCrossModuleIntegration:
    """Smoke tests that wire together all existing contracts in a single flow."""

    def test_mvp_spec_loads(self) -> None:
        from market_intel.mvp_requirements import load_mvp_spec
        spec = load_mvp_spec()
        assert spec is not None

    def test_acceptance_plan_covers_all_mvp_requirements(self) -> None:
        from market_intel.mvp_requirements import load_mvp_spec
        from market_intel.acceptance_test_plan import load_acceptance_test_plan
        mvp_ids = {r.id for r in load_mvp_spec().requirements}
        covered = set()
        for case in load_acceptance_test_plan().cases:
            covered.update(case.covers)
        assert mvp_ids.issubset(covered), (
            f"ATP does not cover MVP requirements: {mvp_ids - covered}"
        )

    def test_release_readiness_spec_compatible_with_production_release_spec(self) -> None:
        from market_intel.production_release_requirements import load_production_release_spec
        prod_spec = load_production_release_spec()
        rr_spec = load_release_readiness_spec()
        prod_categories = {r.category for r in prod_spec.requirements}
        gate_categories = {g.category for g in rr_spec.deployment_gates}
        assert prod_categories.issubset(gate_categories | {"performance"}), (
            "Release readiness gates should cover all production release categories"
        )

    def test_valid_forecast_passes_mvp_validation(self) -> None:
        from market_intel.mvp_requirements import validate_forecast_shape
        forecast = {
            "symbol": "AAPL",
            "predicted_open": 175.50,
            "forecast_for": "2026-08-12",
            "confidence": 0.87,
            "generated_at": "2026-08-11T10:00:00Z",
        }
        validate_forecast_shape(forecast)

    def test_valid_atp_result_passes_validation(self) -> None:
        from market_intel.acceptance_test_plan import validate_test_result
        result = {
            "case_id": "ATP-C1",
            "status": "passed",
            "executed_at": "2026-08-11T10:00:00Z",
            "evidence": "Observation accepted, forecast generated successfully",
        }
        validate_test_result(result)

    def test_full_e2e_happy_path_all_atp_cases_pass(self) -> None:
        from market_intel.acceptance_test_plan import load_acceptance_test_plan, validate_test_result
        plan = load_acceptance_test_plan()
        for case in plan.cases:
            result = {
                "case_id": case.id,
                "status": "passed",
                "executed_at": "2026-08-11T10:00:00Z",
                "evidence": f"E2E run: {case.title} verified",
            }
            validate_test_result(result)

    def test_e2e_failure_path_billing_error_result_is_valid(self) -> None:
        spec = load_release_readiness_spec()
        failure_flows = [f for f in spec.flows if f.flow_type == "failure_path"]
        assert failure_flows, "No failure_path flows found in release readiness spec"
        flow = failure_flows[0]
        result = {
            "flow_id": flow.id,
            "status": "failed",
            "executed_at": "2026-08-11T10:00:00Z",
            "evidence": "Billing service returned 402; forecast generation halted as expected",
        }
        validate_e2e_flow_result(result)

    def test_deployment_readiness_payload_verified(self) -> None:
        spec = load_release_readiness_spec()
        payload = {field: "verified-2026-08-11" for field in spec.required_readiness_fields}
        validate_deployment_readiness(payload)

    def test_post_measure_requirements_compatible(self) -> None:
        from market_intel.post_measure_requirements import (
            load_post_measure_spec,
            validate_measure_result,
        )
        spec = load_post_measure_spec()
        measure = {
            "measure_id": spec.requirements[0].id,
            "metric_value": "98.5",
            "measured_at": "2026-08-11T10:00:00Z",
            "data_source": "live-feed-v2",
            "confidence_score": "0.95",
        }
        validate_measure_result(measure)

    def test_market_intensity_integration(self) -> None:
        from market_intel.market_intensity_agent import analyze_market_intensity
        analysis = {
            "signal_id": "MIA-R1",
            "symbol": "AAPL",
            "intensity_score": "0.72",
            "intensity_level": "high",
            "timestamp": "2026-08-11T10:00:00Z",
        }
        analyze_market_intensity(analysis)
