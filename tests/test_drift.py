from datetime import datetime, timedelta, timezone

from hia.drift import QualificationSnapshot, assess_long_window


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
