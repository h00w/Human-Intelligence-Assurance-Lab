from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from hia.drift import QualificationSnapshot, assess_long_window


@pytest.mark.parametrize("field,value", [
    ("mean_latency_ms", float("nan")), ("p95_latency_ms", float("inf")),
    ("mean_latency_ms", -1), ("p95_latency_ms", True),
    ("provider_errors", -1), ("blocker_failures", False), ("truncations", 0.5),
])
def test_invalid_long_window_evidence_cannot_ship(field, value):
    snapshots = [_snapshot(0), _snapshot(4), replace(_snapshot(8), **{field: value})]
    with pytest.raises(ValueError, match="snapshot"):
        assess_long_window(snapshots)


def test_duplicate_windows_cannot_satisfy_minimum_window_count():
    duplicate = replace(_snapshot(0), mean_latency_ms=1200)
    with pytest.raises(ValueError, match="unique timestamps"):
        assess_long_window([_snapshot(0), duplicate, _snapshot(8)])


def test_naive_timestamps_are_rejected_before_window_sorting():
    naive = replace(_snapshot(4), timestamp=datetime(2026, 9, 5))  # noqa: DTZ001
    with pytest.raises(ValueError, match="timestamp"):
        assess_long_window([_snapshot(0), naive, _snapshot(8)])


def _snapshot(day: int, decision: str = "SHIP"):
    return QualificationSnapshot(
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc) + timedelta(days=day),
        production_decision=decision,
        mean_latency_ms=1400,
        p95_latency_ms=2800,
        blocker_failures=0,
        provider_errors=0,
        truncations=0,
        redundant_cost_rate=0.12,
    )


def test_long_window_waits_for_time_separation():
    report = assess_long_window([_snapshot(0), _snapshot(1), _snapshot(2)])
    assert report.status == "WAITING"
    assert report.ready is False


def test_long_window_can_ship_after_three_windows_over_week():
    report = assess_long_window([_snapshot(0), _snapshot(4), _snapshot(8)])
    assert report.status == "SHIP"
    assert report.ready is True
    assert report.ship_rate == 1.0


def test_long_window_holds_on_regression():
    bad = QualificationSnapshot(
        timestamp=datetime(2026, 9, 9, tzinfo=timezone.utc),
        production_decision="HOLD",
        mean_latency_ms=5100,
        p95_latency_ms=9000,
        blocker_failures=0,
        provider_errors=1,
        truncations=0,
    )
    report = assess_long_window([_snapshot(0), _snapshot(4), bad])
    assert report.status == "HOLD"
    assert report.ready is False


@pytest.mark.parametrize("field,value", [
    ("minimum_windows", True), ("minimum_windows", 0), ("minimum_windows", 1.5),
    ("minimum_span_days", -1), ("max_mean_latency_ms", float("nan")),
    ("max_p95_latency_ms", float("inf")),
])
def test_invalid_qualification_policy_is_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        assess_long_window([_snapshot(0), _snapshot(4), _snapshot(8)], **{field: value})
