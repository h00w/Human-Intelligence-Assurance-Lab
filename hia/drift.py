from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean


@dataclass(frozen=True, slots=True)
class QualificationSnapshot:
    timestamp: datetime
    production_decision: str
    mean_latency_ms: float
    p95_latency_ms: float
    blocker_failures: int
    provider_errors: int
    truncations: int
    redundant_cost_rate: float | None = None


@dataclass(frozen=True, slots=True)
class LongWindowReport:
    window_count: int
    span_days: float
    ship_rate: float
    mean_latency_ms: float
    worst_p95_latency_ms: float
    ready: bool
    status: str
    reasons: tuple[str, ...]


def assess_long_window(
    snapshots: list[QualificationSnapshot],
    *,
    minimum_windows: int = 3,
    minimum_span_days: float = 7.0,
    max_mean_latency_ms: float = 5000.0,
    max_p95_latency_ms: float = 8000.0,
) -> LongWindowReport:
    if not snapshots:
        return LongWindowReport(0, 0.0, 0.0, 0.0, 0.0, False, "WAITING", ("no time-separated snapshots",))
    ordered = sorted(snapshots, key=lambda row: row.timestamp)
    span_days = (ordered[-1].timestamp - ordered[0].timestamp).total_seconds() / 86400
    ship_rate = sum(row.production_decision == "SHIP" for row in ordered) / len(ordered)
    reasons: list[str] = []
    hard_failure = False
    if len(ordered) < minimum_windows:
        reasons.append(f"need at least {minimum_windows} qualification windows")
    if span_days < minimum_span_days:
        reasons.append(f"need at least {minimum_span_days:g} days of observation")
    for row in ordered:
        if row.production_decision != "SHIP" or row.blocker_failures or row.provider_errors or row.truncations:
            hard_failure = True
        if row.mean_latency_ms > max_mean_latency_ms or row.p95_latency_ms > max_p95_latency_ms:
            hard_failure = True
    if hard_failure:
        reasons.append("one or more windows violated the production contract")
    ready = not reasons
    status = "SHIP" if ready else ("HOLD" if hard_failure else "WAITING")
    return LongWindowReport(
        window_count=len(ordered),
        span_days=round(span_days, 3),
        ship_rate=round(ship_rate, 4),
        mean_latency_ms=round(mean(row.mean_latency_ms for row in ordered), 2),
        worst_p95_latency_ms=round(max(row.p95_latency_ms for row in ordered), 2),
        ready=ready,
        status=status,
        reasons=tuple(reasons),
    )
