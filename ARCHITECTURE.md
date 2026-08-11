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
