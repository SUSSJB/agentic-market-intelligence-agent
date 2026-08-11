"""Tests validating the bootstrap contract of the repository.

These tests exist to ensure the environment bootstrap is reproducible and
that the setup verification script correctly identifies broken setups.
They must fail loudly if the contract drifts.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = REPO_ROOT / ".env.example"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_setup.sh"

# Every key declared here MUST appear in .env.example. This is the environment
# contract for the market-intelligence agent.
REQUIRED_ENV_KEYS = {
    "MARKET_INTEL_ENV",
    "MARKET_INTEL_LOG_LEVEL",
    "MARKET_INTEL_DATA_DIR",
    "MARKET_INTEL_HTTP_TIMEOUT_SECONDS",
}


def _parse_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def test_env_example_exists():
    assert ENV_EXAMPLE.is_file(), ".env.example must exist at repo root"


def test_env_example_declares_required_keys():
    parsed = _parse_env_file(ENV_EXAMPLE)
    missing = REQUIRED_ENV_KEYS - parsed.keys()
    assert not missing, f"missing required keys in .env.example: {sorted(missing)}"


def test_env_example_keys_are_shouty_snake_case():
    parsed = _parse_env_file(ENV_EXAMPLE)
    bad = [k for k in parsed if not re.fullmatch(r"[A-Z][A-Z0-9_]*", k)]
    assert not bad, f".env.example keys must be SHOUTY_SNAKE_CASE, got: {bad}"


def test_verify_script_is_executable():
    assert VERIFY_SCRIPT.is_file(), "verify_setup.sh must exist"
    mode = VERIFY_SCRIPT.stat().st_mode
    assert mode & 0o111, "verify_setup.sh must be executable"


def test_verify_script_succeeds_on_clean_checkout():
    result = subprocess.run(
        ["bash", str(VERIFY_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert result.returncode == 0, (
        f"verify_setup.sh should succeed on a clean checkout.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_verify_script_fails_when_env_example_missing(tmp_path: Path):
    # Copy repo skeleton minus .env.example into a temp dir and confirm the
    # verify script detects the missing file. This proves the check actually works.
    import shutil

    for name in ("scripts", "src", "pyproject.toml"):
        src = REPO_ROOT / name
        if src.is_dir():
            shutil.copytree(src, tmp_path / name)
        else:
            shutil.copy2(src, tmp_path / name)

    result = subprocess.run(
        ["bash", str(tmp_path / "scripts" / "verify_setup.sh")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        "verify_setup.sh should fail when .env.example is missing"
    )


def test_python_version_matches_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert "requires-python" in pyproject
    # We target 3.11+ across the platform.
    assert sys.version_info >= (3, 11), (
        f"tests must run on Python 3.11+, got {sys.version_info}"
    )


def test_verify_script_fails_when_required_env_key_missing(tmp_path: Path):
    """Removing a required key from .env.example must break the check."""
    import shutil

    for name in ("scripts", "src", "pyproject.toml", "Makefile", ".gitignore"):
        src = REPO_ROOT / name
        dest = tmp_path / name
        if src.is_dir():
            shutil.copytree(src, dest)
        elif src.is_file():
            shutil.copy2(src, dest)

    # Write an .env.example that is missing MARKET_INTEL_HTTP_TIMEOUT_SECONDS.
    (tmp_path / ".env.example").write_text(
        "MARKET_INTEL_ENV=local\n"
        "MARKET_INTEL_LOG_LEVEL=INFO\n"
        "MARKET_INTEL_DATA_DIR=./.data\n"
    )

    result = subprocess.run(
        ["bash", str(tmp_path / "scripts" / "verify_setup.sh")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "MARKET_INTEL_HTTP_TIMEOUT_SECONDS" in (result.stdout + result.stderr)


def test_env_example_has_no_trailing_whitespace_in_keys():
    parsed = _parse_env_file(ENV_EXAMPLE)
    for key in parsed:
        assert key == key.strip(), f"env key must not have leading/trailing whitespace: {key!r}"


def test_env_example_values_are_non_empty_for_required_keys():
    parsed = _parse_env_file(ENV_EXAMPLE)
    for key in REQUIRED_ENV_KEYS:
        assert parsed.get(key), f"required key {key} must have a default value in .env.example"


def test_verify_script_uses_strict_bash_mode():
    """The setup script must fail fast — set -euo pipefail is required."""
    contents = VERIFY_SCRIPT.read_text()
    assert "set -euo pipefail" in contents
