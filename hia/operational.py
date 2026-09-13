from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OperationalReport:
    passed: bool
    reasons: list[str]


def operational_gate(
    *,
    mean_latency_ms: float | None,
    p95_latency_ms: float | None,
    estimated_cost_usd: float | None,
    provider_errors: int,
    scenario_count: int,
    truncations: int,
    max_mean_latency_ms: float = 5000,
    max_p95_latency_ms: float = 8000,
    max_canary_cost_usd: float = 0.02,
) -> OperationalReport:
    reasons: list[str] = []
    if provider_errors:
        reasons.append(f"provider errors: {provider_errors}")
    if truncations:
        reasons.append(f"completion truncations: {truncations}")
    if mean_latency_ms is not None and mean_latency_ms > max_mean_latency_ms:
        reasons.append(f"mean latency {mean_latency_ms:.0f} ms exceeds {max_mean_latency_ms:.0f} ms")
    if p95_latency_ms is not None and p95_latency_ms > max_p95_latency_ms:
        reasons.append(f"p95 latency {p95_latency_ms:.0f} ms exceeds {max_p95_latency_ms:.0f} ms")
    if estimated_cost_usd is not None and estimated_cost_usd > max_canary_cost_usd:
        reasons.append(f"canary cost ${estimated_cost_usd:.5f} exceeds ${max_canary_cost_usd:.5f}")
    if scenario_count <= 0:
        reasons.append("no scenarios evaluated")
    return OperationalReport(passed=not reasons, reasons=reasons)
