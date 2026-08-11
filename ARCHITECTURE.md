# Architecture

This file is maintained automatically. Each section corresponds to an LLD component.
Entries are appended after each ticket is completed.

## Platform Foundation
- **PRODMARKET-2** Step-001 [INIT] Project bootstrap and environments — .env.example, .gitignore, ARCHITECTURE.md (+9 more)

Established repository bootstrap, environment contracts, CI baseline, and developer
onboarding for the market-intelligence agent (PRODMARKET-2).

**Files:**
- `pyproject.toml` — Python project metadata, dependency groups, tool config (ruff, pytest).
- `.env.example` — canonical list of environment variables required by the agent.
- `.gitignore` — excludes venvs, caches, build artefacts, and secrets.
- `Makefile` — canonical developer entry points: `make setup`, `make verify`, `make test`, `make lint`.
- `scripts/verify_setup.sh` — deterministic setup verification (Python version, required env
  keys present in `.env.example`, presence of core config files, importability of the
  `market_intel` package). Exit code 0 on success, non-zero otherwise; used by both local
  developers and CI.
- `src/market_intel/__init__.py` — package root exposing `__version__`.
- `src/market_intel/config.py` — `Settings` loader that reads env vars with defaults from
  `.env.example` and raises `ConfigError` on missing required keys.
- `tests/test_setup_verification.py` — validates `.env.example` contract, verify script
  exit codes, and reproducibility of bootstrap.
- `tests/test_config.py` — validates `Settings` loader behaviour and error paths.
- `ci-proposed/ci.yml` — CI baseline: runs `make verify` and `make test` on push/PR.
  Lives outside `.github/workflows/` for now; a maintainer with the `workflow` scope
  should move it into `.github/workflows/ci.yml` to activate GitHub Actions.

**Conventions:**
- Python 3.11+, package layout under `src/market_intel/`.
- Tests live under `tests/`, mirroring source structure.
- All required runtime env vars are declared in `.env.example` — the verify script and the
  `Settings` loader treat that file as the single source of truth for the environment contract.

## MVP Requirements
- **PRODMARKET-4** Step-003 [DEV][MVP Requirements] Implement feature behavior to satisfy tests — ARCHITECTURE.md, src/market_intel/mvp_requirements.py, tests/test_mvp_requirements.py
- **PRODMARKET-3** Step-002 [TDD][MVP Requirements] Create failing tests and coverage — ARCHITECTURE.md, src/market_intel/mvp_requirements.py, tests/test_mvp_requirements.py
- **PRODMARKET-3** Step-002 [TDD] Failing tests and coverage — src/market_intel/mvp_requirements.py, tests/test_mvp_requirements.py

Introduced the test-first scaffolding for the MVP contract of the
next-open forecast (PRODMARKET-3).

**Files:**
- `src/market_intel/mvp_requirements.py` — contract stubs only:
  `Requirement` and `MVPSpec` frozen dataclasses, `RequirementsError`
  (subclasses `ValueError`), and `load_mvp_spec()` /
  `validate_forecast_shape()` factories that raise `NotImplementedError`
  until the implementation ticket lands.
- `tests/test_mvp_requirements.py` — 21 tests. Three dataclass-shape and
  error-type tests pass today and lock the public contract. Eighteen
  behaviour tests are marked
  `pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="Pending PRODMARKET-4 …")`
  so CI stays deterministic (green) while the implementation is open;
  once the implementation makes any of them pass, `strict=True` flips it
  to XPASS and turns CI red until the marker is removed — forcing the
  follow-up PR to actually delete the pending markers.

**Conventions:**
- New agent-domain modules live under `src/market_intel/<component>.py` with
  a matching `tests/test_<component>.py`, mirroring the layout established
  by `config.py` / `test_config.py`.
- TDD scaffolding tickets should ship failing tests as
  `xfail(strict=True, raises=<expected error>)` so the CI signal is
  deterministic and future PRs cannot silently leave stale xfail markers
  in place.

- **PRODMARKET-4** Step-003 [DEV] Implement feature behavior to satisfy tests — src/market_intel/mvp_requirements.py, tests/test_mvp_requirements.py

Delivered the production implementation of the MVP contract for the
next-open forecast and unblocked the previously xfailed behaviour tests
(PRODMARKET-4).

**Files:**
- `src/market_intel/mvp_requirements.py` — real implementations of
  `load_mvp_spec()` and `validate_forecast_shape()`. The spec now returns
  a deterministic `MVPSpec` with the required OHLCV input contract, the
  five-field forecast output contract, and four canonical `Requirement`
  entries (`MVP-R1..MVP-R4`) spanning the `input`, `output`, `behaviour`,
  and `operability` categories — including MVP-R3 for delivering detailed
  market-movement insights to financial analysts.
- `tests/test_mvp_requirements.py` — the 18 behaviour tests introduced in
  PRODMARKET-3 have had their `xfail(strict=True, raises=NotImplementedError)`
  markers removed and now assert real behaviour on every run. Two
  additional coverage tests were added: one edge case (`{}` payload lists
  every missing field in the error message) and one contract test
  confirming non-string, non-empty values (e.g. `float`, `0.0`) are
  accepted for numeric output fields. Full file: 23 tests, all passing.

**Behaviour highlights:**
- `load_mvp_spec()` is a pure factory over module-level constants, so
  repeated calls return equal `MVPSpec` instances (satisfies the
  determinism requirement).
- `validate_forecast_shape(payload)` rejects non-dicts, missing required
  output fields (naming every missing field in the error message), and
  empty required values (`None` or empty string). Extra fields on a
  payload are permitted so downstream enrichers can attach debug metadata
  without breaking validation.

## Acceptance Test Plan
- **PRODMARKET-6** Step-005 [DEV][Acceptance Test Plan] Implement feature behavior to satisfy tests — ARCHITECTURE.md, src/market_intel/acceptance_test_plan.py, tests/test_acceptance_test_plan.py
- **PRODMARKET-5** Step-004 [TDD][Acceptance Test Plan] Create failing tests and coverage — src/market_intel/acceptance_test_plan.py, tests/test_acceptance_test_plan.py

Introduced the test-first scaffolding for the Acceptance Test Plan (ATP)
of the market-intelligence agent (PRODMARKET-5).

**Files:**
- `src/market_intel/acceptance_test_plan.py` — contract stubs only:
  `AcceptanceCase` and `AcceptanceTestPlan` frozen dataclasses,
  `TestPlanError` (subclasses `ValueError`, carries `__test__ = False` so
  pytest ignores it during collection), and `load_acceptance_test_plan()`
  / `validate_test_result()` factories that raise `NotImplementedError`
  until the implementation ticket lands.
- `tests/test_acceptance_test_plan.py` — 39 tests. Six dataclass-shape,
  hashability, immutability, error-type, and module-surface tests pass
  today and lock the public contract. Thirty-three behaviour tests are
  marked `pytest.mark.xfail(strict=True, raises=NotImplementedError,
  reason="Pending Acceptance Test Plan implementation ticket")` so CI
  stays deterministic (green) while the implementation is open; once the
  implementation makes any of them pass, `strict=True` flips it to XPASS
  and turns CI red until the marker is removed — forcing the follow-up
  PR to actually delete the pending markers.

**Behaviour intent locked by the pending tests:**
- `load_acceptance_test_plan()` returns a deterministic
  `AcceptanceTestPlan` with non-empty ordered cases, unique ids, GWT
  (given/when/then) clauses filled in, categories drawn from
  `{happy_path, edge_case, regression}`, coverage that includes at least
  one `happy_path` and one `edge_case` case, and a
  `required_result_fields` contract of at least
  `{case_id, status, executed_at, evidence}`.
- The ATP anchors to the MVP contract: every MVP requirement id shipped
  under PRODMARKET-4 (`MVP-R1..MVP-R4`) is covered by at least one case
  via its `covers` tuple.
- `validate_test_result(payload)` accepts any dict carrying the required
  fields, a `case_id` present in the plan, and a `status` from
  `{passed, failed, skipped}`. It rejects non-dicts (naming the actual
  type), missing fields (aggregating every offending field into the
  error), empty required values (`None` or empty string), unknown
  `case_id`s (naming the value), and disallowed statuses — all via
  `TestPlanError`. Extra fields are permitted and the payload is not
  mutated.

**Conventions:**
- ATP scaffolding follows the TDD convention introduced by PRODMARKET-3:
  behaviour tests ship as `xfail(strict=True, raises=NotImplementedError)`
  so future PRs cannot silently leave stale xfail markers in place.
- Any exception class whose name starts with `Test` (e.g.
  `TestPlanError`) must carry `__test__ = False` so pytest does not try
  to collect it as a test class.

- **PRODMARKET-6** Step-005 [DEV][Acceptance Test Plan] Implement feature behavior to satisfy tests — src/market_intel/acceptance_test_plan.py, tests/test_acceptance_test_plan.py

Delivered the production implementation of the Acceptance Test Plan (ATP)
and unblocked the previously xfailed behaviour tests (PRODMARKET-6).

**Files:**
- `src/market_intel/acceptance_test_plan.py` — real implementations of
  `load_acceptance_test_plan()` and `validate_test_result()`. The plan returns
  a deterministic `AcceptanceTestPlan` with 7 `AcceptanceCase` entries
  spanning `happy_path`, `edge_case`, and `regression` categories, every
  MVP requirement (MVP-R1..MVP-R4) covered by at least one case, unique
  non-empty ids (ATP-C1..ATP-C7), GWT clauses filled in, and
  `required_result_fields` of `(case_id, status, executed_at, evidence)`.
- `tests/test_acceptance_test_plan.py` — the 33 behaviour tests introduced
  in PRODMARKET-5 have had their `xfail(strict=True, raises=NotImplementedError)`
  markers removed and now assert real behaviour on every run. Full file:
  39 tests, all passing.

**Behaviour highlights:**
- `load_acceptance_test_plan()` is a pure factory over module-level constants,
  so repeated calls return equal `AcceptanceTestPlan` instances (satisfies
  the determinism requirement).
- `validate_test_result(payload)` rejects non-dicts (naming the actual type),
  missing required fields (aggregating every offending field into the error),
  empty required values (`None` or empty string), unknown `case_id`s (naming
  the value), and disallowed statuses. Extra fields are permitted and the
  payload is not mutated.
- Acceptance intent satisfied: financial analysts receive detailed market
  movement insights via ATP-C3 (happy_path, covers MVP-R3).

## Production Release Requirements
- **PRODMARKET-8** Step-007 [DEV][Production Release Requirements] Implement feature behavior to satisfy tests — src/market_intel/production_release_requirements.py, tests/test_production_release_requirements.py
- **PRODMARKET-7** Step-006 [TDD][Production Release Requirements] Create failing tests and coverage — ARCHITECTURE.md, src/market_intel/production_release_requirements.py, tests/test_production_release_requirements.py
- **PRODMARKET-7** Step-006 [TDD][Production Release Requirements] Create failing tests and coverage — src/market_intel/production_release_requirements.py, tests/test_production_release_requirements.py

Introduced the test-first scaffolding for the Production Release Requirements (PRR)
contract of the market-intelligence agent (PRODMARKET-7).

**Files:**
- `src/market_intel/production_release_requirements.py` — contract stubs only:
  `ReleaseRequirement` and `ProductionReleaseSpec` frozen dataclasses,
  `ReleaseRequirementsError` (subclasses `ValueError`), and
  `load_production_release_spec()` / `validate_release_readiness()` factories
  that raise `NotImplementedError` until the implementation ticket lands.
- `tests/test_production_release_requirements.py` — 41 tests. Six dataclass-shape,
  hashability, immutability, error-type, and module-surface tests pass today and
  lock the public contract. Thirty-five behaviour tests are marked
  `pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="Pending PRODMARKET-8 …")`
  so CI stays deterministic (green) while the implementation is open; once the
  implementation makes any of them pass, `strict=True` flips it to XPASS and
  turns CI red until the marker is removed — forcing the follow-up PR to actually
  delete the pending markers.

**Conventions:**
- New agent-domain modules live under `src/market_intel/<component>.py` with
  a matching `tests/test_<component>.py`, mirroring the layout established by
  prior components.
- TDD scaffolding tickets ship failing tests as
  `xfail(strict=True, raises=NotImplementedError)` so future PRs cannot silently
  leave stale xfail markers in place.

## Post-Measure Requirements
- **PRODMARKET-10** Step-009 [DEV][Post-Measure Requirements] Implement feature behavior to satisfy tests — src/market_intel/post_measure_requirements.py, tests/test_post_measure_requirements.py
- **PRODMARKET-9** Step-008 [TDD][Post-Measure Requirements] Create failing tests and coverage — ARCHITECTURE.md, src/market_intel/post_measure_requirements.py, tests/test_post_measure_requirements.py
- **PRODMARKET-9** Step-008 [TDD][Post-Measure Requirements] Create failing tests and coverage — src/market_intel/post_measure_requirements.py, tests/test_post_measure_requirements.py

Introduced the test-first scaffolding for the Post-Measure Requirements
contract of the market-intelligence agent (PRODMARKET-9).

**Files:**
- `src/market_intel/post_measure_requirements.py` — contract stubs only:
  `MeasureRequirement` and `PostMeasureSpec` frozen dataclasses,
  `PostMeasureError` (subclasses `ValueError`), and `load_post_measure_spec()`
  / `validate_measure_result()` factories that raise `NotImplementedError`
  until the implementation ticket lands.
- `tests/test_post_measure_requirements.py` — 45 tests. Ten dataclass-shape,
  hashability, immutability, error-type, and module-surface tests pass today
  and lock the public contract. Thirty-five behaviour tests are marked
  `pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="Pending PRODMARKET-10 …")`
  so CI stays deterministic (green) while the implementation is open; once the
  implementation makes any of them pass, `strict=True` flips it to XPASS and
  turns CI red until the marker is removed — forcing the follow-up PR to
  actually delete the pending markers.

**Conventions:**
- New agent-domain modules live under `src/market_intel/<component>.py` with
  a matching `tests/test_<component>.py`, mirroring the layout established by
  prior components.
- TDD scaffolding tickets ship failing tests as
  `xfail(strict=True, raises=NotImplementedError)` so future PRs cannot silently
  leave stale xfail markers in place.

## Market-Intensity Agent
- **PRODMARKET-12** Step-011 [DEV][Market-Intensity Agent] Implement feature behavior to satisfy tests — src/market_intel/market_intensity_agent.py, tests/test_market_intensity_agent.py
- **PRODMARKET-11** Step-010 [TDD][Market-Intensity Agent] Create failing tests and coverage — src/market_intel/market_intensity_agent.py, tests/test_market_intensity_agent.py

## Implementation Roadmap
- **PRODMARKET-14** Step-013 [DEV][Implementation Roadmap] Implement feature behavior to satisfy tests — ARCHITECTURE.md, src/market_intel/implementation_roadmap.py, tests/test_implementation_roadmap.py

## Release Readiness
- **PRODMARKET-15** Step-014 [E2E] End-to-end integration and release readiness — src/market_intel/release_readiness.py, tests/test_release_readiness.py

Delivered the E2E integration and release readiness contract, wiring together all
previously-shipped components into a validated end-to-end journey (PRODMARKET-15).

**Files:**
- `src/market_intel/release_readiness.py` — production implementation exposing:
  `E2EFlow`, `E2EFlowResult`, `DeploymentGate`, `ReleaseReadinessSpec`,
  `ReleaseReadinessError`, `load_release_readiness_spec()`,
  `validate_e2e_flow_result()`, and `validate_deployment_readiness()`.
- `tests/test_release_readiness.py` — 58 tests covering module surface, spec
  behaviour, flow-result validation, deployment-readiness validation, and
  cross-module integration smoke tests that wire together MVP, ATP, production
  release, post-measure, market-intensity, and release-readiness contracts.

**Behaviour highlights:**
- `load_release_readiness_spec()` returns a deterministic `ReleaseReadinessSpec`
  with 6 `E2EFlow` entries spanning `happy_path`, `failure_path`, `resiliency`,
  and `billing` types, and 5 `DeploymentGate` entries covering quality, security,
  operability (x2), and performance categories.
- `validate_e2e_flow_result()` enforces required fields, rejects unknown flow ids
  and disallowed statuses, and permits extra metadata fields.
- `validate_deployment_readiness()` aggregates all missing/empty field names into
  a single `ReleaseReadinessError`, covering the full release checklist.
- Rollback strategy: 5-step ordered procedure (revert, restore image tag, notify
  on-call, validate health checks, open post-mortem ticket).
- Cross-module integration: all MVP requirements are covered by ATP cases; all
  production release categories are covered by deployment gates.
