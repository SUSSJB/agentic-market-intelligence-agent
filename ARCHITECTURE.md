# Architecture

This file is maintained automatically. Each section corresponds to an LLD component.
Entries are appended after each ticket is completed.

## Platform Foundation

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
- `.github/workflows/ci.yml` — CI baseline: runs `make verify` and `make test` on push/PR.

**Conventions:**
- Python 3.11+, package layout under `src/market_intel/`.
- Tests live under `tests/`, mirroring source structure.
- All required runtime env vars are declared in `.env.example` — the verify script and the
  `Settings` loader treat that file as the single source of truth for the environment contract.
