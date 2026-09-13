from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Any

from .adapters.base import ModelAdapter
from .resilience import HedgedAdapter

RISK_ORDER = ("critical", "high", "medium", "low")


@dataclass(frozen=True, slots=True)
class LatencyProfile:
    sample_count: int
    p50_ms: float
    p75_ms: float
    p90_ms: float
    p95_ms: float


@dataclass(frozen=True, slots=True)
class AdaptiveHedgePolicy:
    latency: LatencyProfile
    delays_ms: dict[str, float]
    min_delay_ms: float = 500.0
    max_delay_ms: float = 2500.0

    @classmethod
    def from_latencies(
        cls,
        latencies_ms: list[float],
        *,
        min_delay_ms: float = 500.0,
        max_delay_ms: float = 2500.0,
    ) -> AdaptiveHedgePolicy:
        if len(latencies_ms) < 4:
            raise ValueError("adaptive hedge policy requires at least four latency samples")
        values = sorted(float(value) for value in latencies_ms)

        def percentile(q: float) -> float:
            index = max(0, min(len(values) - 1, math.ceil(q * len(values)) - 1))
            return values[index]

        profile = LatencyProfile(
            sample_count=len(values),
            p50_ms=round(percentile(0.50), 2),
            p75_ms=round(percentile(0.75), 2),
            p90_ms=round(percentile(0.90), 2),
            p95_ms=round(percentile(0.95), 2),
        )

        def bounded(value: float) -> float:
            return round(max(min_delay_ms, min(max_delay_ms, value)), 2)

        delays = {
            "critical": bounded(profile.p50_ms),
            "high": bounded(profile.p75_ms),
            "medium": bounded(profile.p90_ms),
            "low": bounded(profile.p95_ms),
        }
        return cls(
            latency=profile,
            delays_ms=delays,
            min_delay_ms=min_delay_ms,
            max_delay_ms=max_delay_ms,
        )

    def delay_for(self, risk_level: str) -> float:
        return self.delays_ms.get(risk_level, self.delays_ms["medium"])


def fallback_timeout_budget_s(
    hedge_delay_ms: float,
    *,
    p95_slo_ms: float = 8000.0,
    safety_margin_ms: float = 500.0,
    min_timeout_s: float = 4.0,
    max_timeout_s: float = 6.5,
) -> float:
    """Derive the fallback request deadline from the end-to-end p95 budget.

    The fallback starts after ``hedge_delay_ms``. Its request deadline is bounded so the
    configured path still leaves a fixed safety margin before the 8-second production p95
    ceiling. The production gate remains authoritative if actual latency violates the SLO.
    """
    available_ms = p95_slo_ms - hedge_delay_ms - safety_margin_ms
    timeout_s = available_ms / 1000
    return round(max(min_timeout_s, min(max_timeout_s, timeout_s)), 3)


class AdaptiveHedgedAdapter(ModelAdapter):
    """Risk-aware hedging using delays derived from measured primary latency."""

    provider = "adaptive-hedged"

    def __init__(
        self,
        primary: ModelAdapter,
        fallback: ModelAdapter,
        *,
        policy: AdaptiveHedgePolicy,
        risk_by_prompt: dict[str, str],
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.policy = policy
        self.risk_by_prompt = dict(risk_by_prompt)
        self.model = primary.model

    def generate(self, *, system_prompt: str, user_prompt: str):
        risk = self.risk_by_prompt.get(user_prompt, "medium")
        delay_ms = self.policy.delay_for(risk)
        result = HedgedAdapter(
            self.primary,
            self.fallback,
            hedge_delay_ms=delay_ms,
        ).generate(system_prompt=system_prompt, user_prompt=user_prompt)
        metadata = dict(result.metadata)
        metadata.update(
            {
                "adaptive_hedging": True,
                "scenario_risk_level": risk,
                "adaptive_hedge_delay_ms": delay_ms,
                "latency_profile": {
                    "sample_count": self.policy.latency.sample_count,
                    "p50_ms": self.policy.latency.p50_ms,
                    "p75_ms": self.policy.latency.p75_ms,
                    "p90_ms": self.policy.latency.p90_ms,
                    "p95_ms": self.policy.latency.p95_ms,
                },
            }
        )
        result.metadata = metadata
        return result


def routing_economics(report: dict[str, Any]) -> dict[str, Any]:
    rows = report.get("evidence", [])
    successful = [row for row in rows if row.get("error") is None]
    hedged = 0
    fallback_wins = 0
    winner_tokens = 0
    observed_tokens = 0
    redundant_tokens = 0
    winner_cost = 0.0
    observed_cost = 0.0
    redundant_cost = 0.0
    priced_rows = 0

    for row in successful:
        generation = row["generation"]
        metadata = generation.get("metadata", {})
        if metadata.get("hedge_used"):
            hedged += 1
        if metadata.get("winning_role") == "fallback":
            fallback_wins += 1

        selected_tokens = generation.get("total_tokens")
        all_tokens = metadata.get("observed_total_tokens")
        if selected_tokens is not None:
            winner_tokens += int(selected_tokens)
        if all_tokens is not None:
            observed_tokens += int(all_tokens)
            redundant_tokens += max(0, int(all_tokens) - int(selected_tokens or 0))

        selected_cost = generation.get("estimated_cost_usd")
        all_cost = metadata.get("observed_estimated_cost_usd")
        if selected_cost is not None and all_cost is not None:
            priced_rows += 1
            winner_cost += float(selected_cost)
            observed_cost += float(all_cost)
            redundant_cost += max(0.0, float(all_cost) - float(selected_cost))

    count = len(successful)
    return {
        "scenario_count": count,
        "hedge_rate": round(hedged / count, 4) if count else 0.0,
        "fallback_winner_rate": round(fallback_wins / count, 4) if count else 0.0,
        "winner_tokens": winner_tokens or None,
        "observed_tokens": observed_tokens or None,
        "redundant_tokens": redundant_tokens,
        "redundant_token_rate": round(redundant_tokens / observed_tokens, 4)
        if observed_tokens
        else 0.0,
        "priced_rows": priced_rows,
        "winner_cost_usd": round(winner_cost, 8) if priced_rows else None,
        "observed_cost_usd": round(observed_cost, 8) if priced_rows else None,
        "redundant_cost_usd": round(redundant_cost, 8) if priced_rows else None,
        "redundant_cost_rate": round(redundant_cost / observed_cost, 4)
        if observed_cost
        else 0.0,
    }


def cohort_metrics(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cohorts: dict[str, list[dict[str, Any]]] = {risk: [] for risk in RISK_ORDER}
    for row in report.get("evidence", []):
        risk = row.get("scenario", {}).get("risk_level", "medium")
        cohorts.setdefault(risk, []).append(row)

    output: dict[str, dict[str, Any]] = {}
    for risk, rows in cohorts.items():
        if not rows:
            continue
        latencies = [
            float(row["generation"]["latency_ms"])
            for row in rows
            if row.get("error") is None
        ]
        economics = routing_economics({"evidence": rows})
        passed = sum(bool(row.get("evaluation", {}).get("passed")) for row in rows)
        output[risk] = {
            "scenario_count": len(rows),
            "pass_rate": round(passed / len(rows), 4),
            "mean_latency_ms": round(mean(latencies), 2) if latencies else None,
            **economics,
        }
    return output
