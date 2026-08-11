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
