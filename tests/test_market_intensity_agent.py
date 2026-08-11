"""Tests for the Market-Intensity Agent contract.

Test intent
-----------
These tests describe the *shape* the Market-Intensity Agent contract must
satisfy for the market-intelligence agent's intensity analysis gate:

* ``load_market_intensity_spec()`` must return a canonical, immutable
  :class:`MarketIntensitySpec` with a stable set of required analysis fields and a
  non-empty ordered list of :class:`MarketSignal` entries spanning
  volume, volatility, momentum, and sentiment categories.
* ``analyze_market_intensity(payload)`` must accept any dict matching the spec's
  ``required_analysis_fields`` and reject non-dicts, missing fields, and empty
  required values with :class:`MarketIntensityError`.

TDD history
-----------
PRODMARKET-11 introduced these tests marked ``xfail(strict=True, ...)`` so CI
stays green while the implementation ticket (PRODMARKET-12) is open.
Once the implementation makes any xfail test pass, ``strict=True`` flips it
to XPASS and turns CI red — forcing the follow-up PR to actually remove the
pending markers.

External deps
-------------
None. Everything is exercised in-process — the module has no I/O and no
network calls, so no mocking is needed.
"""
from __future__ import annotations

import dataclasses

import pytest

from market_intel.market_intensity_agent import (
    MarketIntensityError,
    MarketIntensitySpec,
    MarketSignal,
    analyze_market_intensity,
    load_market_intensity_spec,
)

# ---------------------------------------------------------------------------
# Dataclass shape — locks the public contract (these pass today)
# ---------------------------------------------------------------------------


def test_market_signal_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(MarketSignal)}
    assert field_names == {"id", "title", "description", "category"}
    assert MarketSignal.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_market_intensity_spec_is_frozen_dataclass_with_expected_fields():
    field_names = {f.name for f in dataclasses.fields(MarketIntensitySpec)}
    assert field_names == {"required_analysis_fields", "signals"}
    assert MarketIntensitySpec.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


def test_market_intensity_error_is_valueerror_subclass():
    assert issubclass(MarketIntensityError, ValueError)


def test_market_signal_instance_is_immutable():
    sig = MarketSignal(id="X", title="t", description="d", category="volume")
    with pytest.raises(dataclasses.FrozenInstanceError):
        sig.title = "changed"  # type: ignore[misc]


def test_market_signal_is_hashable():
    sig = MarketSignal(id="X", title="t", description="d", category="volume")
    assert hash(sig) == hash(sig)
    assert {sig} == {sig}


def test_module_exports_expected_public_symbols():
    from market_intel import market_intensity_agent

    assert set(market_intensity_agent.__all__) == {
        "MarketIntensityError",
        "MarketIntensitySpec",
        "MarketSignal",
        "analyze_market_intensity",
        "load_market_intensity_spec",
    }


# ---------------------------------------------------------------------------
# load_market_intensity_spec — behaviour tests (xfail until PRODMARKET-12)
# ---------------------------------------------------------------------------


def test_load_market_intensity_spec_returns_spec_instance():
    spec = load_market_intensity_spec()
    assert isinstance(spec, MarketIntensitySpec)


def test_load_market_intensity_spec_declares_required_analysis_fields():
    spec = load_market_intensity_spec()
    expected = {
        "signal_id",
        "symbol",
        "intensity_score",
        "intensity_level",
        "timestamp",
    }
    assert expected.issubset(set(spec.required_analysis_fields)), (
        f"required_analysis_fields must cover {expected}, "
        f"got {spec.required_analysis_fields}"
    )


def test_load_market_intensity_spec_has_non_empty_ordered_signals():
    spec = load_market_intensity_spec()
    assert isinstance(spec.signals, tuple)
    assert len(spec.signals) >= 1
    assert all(isinstance(s, MarketSignal) for s in spec.signals)


def test_load_market_intensity_spec_signal_ids_are_unique_and_non_empty():
    spec = load_market_intensity_spec()
    ids = [s.id for s in spec.signals]
    assert all(sid for sid in ids), "signal ids must be non-empty"
    assert len(ids) == len(set(ids)), f"signal ids must be unique, got {ids}"


def test_load_market_intensity_spec_categories_are_from_allowed_set():
    spec = load_market_intensity_spec()
    allowed = {"volume", "volatility", "momentum", "sentiment"}
    bad = [s for s in spec.signals if s.category not in allowed]
    assert not bad, f"signals with disallowed category: {bad}"


def test_load_market_intensity_spec_covers_all_allowed_categories():
    spec = load_market_intensity_spec()
    categories = {s.category for s in spec.signals}
    assert categories == {"volume", "volatility", "momentum", "sentiment"}


def test_load_market_intensity_spec_signal_titles_and_descriptions_non_empty():
    spec = load_market_intensity_spec()
    for s in spec.signals:
        assert s.title.strip(), f"signal {s.id} has empty title"
        assert s.description.strip(), f"signal {s.id} has empty description"


def test_load_market_intensity_spec_is_deterministic_across_calls():
    assert load_market_intensity_spec() == load_market_intensity_spec()


def test_load_market_intensity_spec_repeated_calls_have_equal_signals():
    a = load_market_intensity_spec()
    b = load_market_intensity_spec()
    assert a.signals == b.signals
    assert a.required_analysis_fields == b.required_analysis_fields


def test_load_market_intensity_spec_field_containers_are_tuples():
    spec = load_market_intensity_spec()
    assert isinstance(spec.required_analysis_fields, tuple)
    assert isinstance(spec.signals, tuple)


def test_market_intensity_spec_instance_is_immutable():
    spec = load_market_intensity_spec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.required_analysis_fields = ()  # type: ignore[misc]


def test_load_market_intensity_spec_contains_canonical_signal_ids():
    spec = load_market_intensity_spec()
    ids = {s.id for s in spec.signals}
    assert {"MIA-R1", "MIA-R2", "MIA-R3", "MIA-R4"}.issubset(ids)


def test_load_market_intensity_spec_has_volume_signal():
    spec = load_market_intensity_spec()
    volume_signals = [s for s in spec.signals if s.category == "volume"]
    assert volume_signals, "spec must include at least one volume signal"
    text = " ".join((s.title + " " + s.description).lower() for s in volume_signals)
    assert any(kw in text for kw in ("volume", "trading", "liquidity", "activity"))


def test_load_market_intensity_spec_has_volatility_signal():
    spec = load_market_intensity_spec()
    volatility_signals = [s for s in spec.signals if s.category == "volatility"]
    assert volatility_signals, "spec must include at least one volatility signal"
    text = " ".join(
        (s.title + " " + s.description).lower() for s in volatility_signals
    )
    assert any(kw in text for kw in ("volatil", "price", "swing", "fluctuat", "range"))


def test_load_market_intensity_spec_has_momentum_signal():
    spec = load_market_intensity_spec()
    momentum_signals = [s for s in spec.signals if s.category == "momentum"]
    assert momentum_signals, "spec must include at least one momentum signal"
    text = " ".join(
        (s.title + " " + s.description).lower() for s in momentum_signals
    )
    assert any(kw in text for kw in ("momentum", "trend", "direction", "speed", "rate"))


def test_load_market_intensity_spec_has_sentiment_signal():
    spec = load_market_intensity_spec()
    sentiment_signals = [s for s in spec.signals if s.category == "sentiment"]
    assert sentiment_signals, "spec must include at least one sentiment signal"
    text = " ".join(
        (s.title + " " + s.description).lower() for s in sentiment_signals
    )
    assert any(kw in text for kw in ("sentiment", "fear", "greed", "bullish", "bearish", "mood"))


# ---------------------------------------------------------------------------
# analyze_market_intensity — behaviour tests (xfail until PRODMARKET-12)
# ---------------------------------------------------------------------------


def test_analyze_market_intensity_accepts_payload_with_all_required_fields():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.75
    analyze_market_intensity(payload)  # must not raise


def test_analyze_market_intensity_accepts_payload_with_extra_fields():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.5
    payload["debug_note"] = "extra field is fine"
    analyze_market_intensity(payload)


@pytest.mark.parametrize(
    "not_a_dict",
    [None, [], "result", 42, 3.14, ("signal_id", "symbol")],
    ids=["none", "list", "str", "int", "float", "tuple"],
)
def test_analyze_market_intensity_rejects_non_dict_payloads(not_a_dict):
    with pytest.raises(MarketIntensityError):
        analyze_market_intensity(not_a_dict)  # type: ignore[arg-type]


def test_analyze_market_intensity_non_dict_error_names_actual_type():
    with pytest.raises(MarketIntensityError) as exc_info:
        analyze_market_intensity("not a dict")  # type: ignore[arg-type]
    assert "str" in str(exc_info.value)


def test_analyze_market_intensity_rejects_missing_required_field():
    spec = load_market_intensity_spec()
    assert spec.required_analysis_fields, "spec must have at least one required field"
    missing = spec.required_analysis_fields[0]
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.6
    del payload[missing]

    with pytest.raises(MarketIntensityError) as exc_info:
        analyze_market_intensity(payload)
    assert missing in str(exc_info.value)


def test_analyze_market_intensity_rejects_empty_required_value():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.4
    payload[spec.required_analysis_fields[0]] = ""

    with pytest.raises(MarketIntensityError):
        analyze_market_intensity(payload)


def test_analyze_market_intensity_rejects_none_required_value():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.4
    payload[spec.required_analysis_fields[0]] = None

    with pytest.raises(MarketIntensityError):
        analyze_market_intensity(payload)


def test_analyze_market_intensity_rejects_all_fields_missing():
    with pytest.raises(MarketIntensityError) as exc_info:
        analyze_market_intensity({})
    msg = str(exc_info.value)
    spec = load_market_intensity_spec()
    for field in spec.required_analysis_fields:
        assert field in msg


def test_analyze_market_intensity_reports_multiple_missing_fields():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.3
    dropped = list(spec.required_analysis_fields[:2])
    for f in dropped:
        del payload[f]

    with pytest.raises(MarketIntensityError) as exc_info:
        analyze_market_intensity(payload)
    msg = str(exc_info.value)
    for f in dropped:
        assert f in msg


def test_analyze_market_intensity_reports_multiple_empty_fields():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.8
    payload[spec.required_analysis_fields[0]] = ""
    payload[spec.required_analysis_fields[1]] = None

    with pytest.raises(MarketIntensityError) as exc_info:
        analyze_market_intensity(payload)
    msg = str(exc_info.value)
    assert spec.required_analysis_fields[0] in msg
    assert spec.required_analysis_fields[1] in msg


def test_analyze_market_intensity_accepts_numeric_intensity_score():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.95
    analyze_market_intensity(payload)


def test_analyze_market_intensity_accepts_zero_intensity_score():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.0
    analyze_market_intensity(payload)


def test_analyze_market_intensity_accepts_whitespace_string_values():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.5
    payload[spec.required_analysis_fields[0]] = " "
    analyze_market_intensity(payload)


def test_analyze_market_intensity_does_not_mutate_payload():
    spec = load_market_intensity_spec()
    payload = {name: f"value-{name}" for name in spec.required_analysis_fields}
    payload["intensity_score"] = 0.7
    snapshot = dict(payload)
    try:
        analyze_market_intensity(payload)
    except (MarketIntensityError, NotImplementedError):
        pass
    assert payload == snapshot


# ---------------------------------------------------------------------------
# Additional contract tests
# ---------------------------------------------------------------------------


def test_market_signal_equality_between_equal_instances():
    a = MarketSignal(id="M1", title="t", description="d", category="volume")
    b = MarketSignal(id="M1", title="t", description="d", category="volume")
    assert a == b


def test_market_signal_inequality_between_different_instances():
    a = MarketSignal(id="M1", title="t", description="d", category="volume")
    b = MarketSignal(id="M2", title="t", description="d", category="volume")
    assert a != b


def test_market_intensity_error_carries_message():
    msg = "missing field: signal_id"
    err = MarketIntensityError(msg)
    assert str(err) == msg


def test_market_intensity_error_is_catchable_as_valueerror():
    with pytest.raises(ValueError):
        raise MarketIntensityError("bad payload")
