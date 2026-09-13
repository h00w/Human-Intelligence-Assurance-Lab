from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CandidateSummary:
    name: str
    decision: str
    pass_rate: float
    semantic_score: float | None
    mean_latency_ms: float | None
    estimated_cost_usd: float | None
    blocker_failures: int = 0


@dataclass(frozen=True, slots=True)
class PairwiseComparison:
    winner: str
    rationale: list[str]


def compare_candidates(a: CandidateSummary, b: CandidateSummary) -> PairwiseComparison:
    reasons: list[str] = []

    if a.blocker_failures != b.blocker_failures:
        winner = a if a.blocker_failures < b.blocker_failures else b
        reasons.append("fewer blocker failures")
        return PairwiseComparison(winner=winner.name, rationale=reasons)

    decision_rank = {"SHIP": 2, "INVESTIGATE": 1, "HOLD": 0}
    if decision_rank.get(a.decision, -1) != decision_rank.get(b.decision, -1):
        winner = a if decision_rank.get(a.decision, -1) > decision_rank.get(b.decision, -1) else b
        reasons.append("stronger release decision")
        return PairwiseComparison(winner=winner.name, rationale=reasons)

    if abs(a.pass_rate - b.pass_rate) >= 0.02:
        winner = a if a.pass_rate > b.pass_rate else b
        reasons.append("higher deterministic pass rate")
        return PairwiseComparison(winner=winner.name, rationale=reasons)

    if a.semantic_score is not None and b.semantic_score is not None and abs(a.semantic_score - b.semantic_score) >= 0.05:
        winner = a if a.semantic_score > b.semantic_score else b
        reasons.append("higher calibrated semantic quality")
        return PairwiseComparison(winner=winner.name, rationale=reasons)

    if (
        a.mean_latency_ms is not None
        and b.mean_latency_ms is not None
        and a.mean_latency_ms != b.mean_latency_ms
    ):
        winner = a if a.mean_latency_ms < b.mean_latency_ms else b
        reasons.append("lower mean latency after safety/quality parity")
        return PairwiseComparison(winner=winner.name, rationale=reasons)

    if (
        a.estimated_cost_usd is not None
        and b.estimated_cost_usd is not None
        and a.estimated_cost_usd != b.estimated_cost_usd
    ):
        winner = a if a.estimated_cost_usd < b.estimated_cost_usd else b
        reasons.append("lower estimated cost after safety/quality parity")
        return PairwiseComparison(winner=winner.name, rationale=reasons)

    return PairwiseComparison(winner="TIE", rationale=["no material difference under current thresholds"])
