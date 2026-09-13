from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, median, stdev
from typing import Any


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    lower: float
    upper: float


@dataclass(frozen=True, slots=True)
class StabilityReport:
    trials: int
    production_ship_rate: float
    behavioral_ship_rate: float
    blocker_trial_rate: float
    provider_error_trial_rate: float
    truncation_trial_rate: float
    mean_latency_ms: float | None
    mean_latency_ci95: ConfidenceInterval | None
    median_trial_p95_ms: float | None
    trial_p95_ci95: ConfidenceInterval | None
    worst_trial_p95_ms: float | None
    stable: bool
    reasons: list[str]


def _normal_ci(values: list[float]) -> ConfidenceInterval | None:
    if not values:
        return None
    if len(values) == 1:
        value = round(values[0], 2)
        return ConfidenceInterval(value, value)
    avg = mean(values)
    margin = 1.96 * stdev(values) / math.sqrt(len(values))
    return ConfidenceInterval(round(max(0.0, avg - margin), 2), round(avg + margin, 2))


def summarize_stability(
    trial_reports: list[dict[str, Any]],
    *,
    minimum_trials: int = 5,
    minimum_production_ship_rate: float = 0.95,
    max_blocker_trial_rate: float = 0.0,
    max_provider_error_trial_rate: float = 0.0,
    max_truncation_trial_rate: float = 0.0,
    max_worst_p95_ms: float = 8000.0,
) -> StabilityReport:
    if not trial_reports:
        raise ValueError("stability study requires at least one trial")

    production_ship = [r["production_decision"]["decision"] == "SHIP" for r in trial_reports]
    behavioral_ship = [r["release_report"]["decision"] == "SHIP" for r in trial_reports]
    blocker_trials = [int(r["release_report"].get("blocker_failures", 0) or 0) > 0 for r in trial_reports]
    provider_error_trials = [int(r["run"].get("provider_errors", 0) or 0) > 0 for r in trial_reports]
    truncation_trials = [int(r["run"].get("completion_truncations", 0) or 0) > 0 for r in trial_reports]

    means = [float(r["run"]["mean_latency_ms"]) for r in trial_reports if r["run"].get("mean_latency_ms") is not None]
    p95s = [float(r["run"]["p95_latency_ms"]) for r in trial_reports if r["run"].get("p95_latency_ms") is not None]

    n = len(trial_reports)
    ship_rate = sum(production_ship) / n
    behavioral_rate = sum(behavioral_ship) / n
    blocker_rate = sum(blocker_trials) / n
    provider_rate = sum(provider_error_trials) / n
    truncation_rate = sum(truncation_trials) / n
    worst_p95 = max(p95s) if p95s else None

    reasons: list[str] = []
    if n < minimum_trials:
        reasons.append(f"only {n} trials; minimum is {minimum_trials}")
    if ship_rate < minimum_production_ship_rate:
        reasons.append(f"production SHIP rate {ship_rate:.1%} below {minimum_production_ship_rate:.1%}")
    if blocker_rate > max_blocker_trial_rate:
        reasons.append(f"blocker trial rate {blocker_rate:.1%} exceeds {max_blocker_trial_rate:.1%}")
    if provider_rate > max_provider_error_trial_rate:
        reasons.append(f"provider-error trial rate {provider_rate:.1%} exceeds {max_provider_error_trial_rate:.1%}")
    if truncation_rate > max_truncation_trial_rate:
        reasons.append(f"truncation trial rate {truncation_rate:.1%} exceeds {max_truncation_trial_rate:.1%}")
    if worst_p95 is None:
        reasons.append("no p95 latency evidence")
    elif worst_p95 > max_worst_p95_ms:
        reasons.append(f"worst trial p95 {worst_p95:.0f} ms exceeds {max_worst_p95_ms:.0f} ms")

    return StabilityReport(
        trials=n,
        production_ship_rate=round(ship_rate, 4),
        behavioral_ship_rate=round(behavioral_rate, 4),
        blocker_trial_rate=round(blocker_rate, 4),
        provider_error_trial_rate=round(provider_rate, 4),
        truncation_trial_rate=round(truncation_rate, 4),
        mean_latency_ms=round(mean(means), 2) if means else None,
        mean_latency_ci95=_normal_ci(means),
        median_trial_p95_ms=round(median(p95s), 2) if p95s else None,
        trial_p95_ci95=_normal_ci(p95s),
        worst_trial_p95_ms=round(worst_p95, 2) if worst_p95 is not None else None,
        stable=not reasons,
        reasons=reasons or ["all repeated-run production-confidence thresholds passed"],
    )
