"""Package-level tests for `market_intel`."""
from __future__ import annotations

import re

import market_intel


def test_package_exposes_version():
    assert hasattr(market_intel, "__version__")
    assert isinstance(market_intel.__version__, str)
    assert market_intel.__version__


def test_package_version_is_semver_shaped():
    # Loose semver check: MAJOR.MINOR.PATCH with optional pre-release suffix.
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-.].+)?", market_intel.__version__)


def test_package_declares_public_api():
    assert "__version__" in market_intel.__all__


def test_package_version_matches_pyproject():
    from pathlib import Path

    pyproject = (
        Path(__file__).resolve().parents[1] / "pyproject.toml"
    ).read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match, "pyproject.toml must declare a version"
    assert match.group(1) == market_intel.__version__
