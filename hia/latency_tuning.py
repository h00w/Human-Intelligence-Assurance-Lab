from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LatencyProfile:
    name: str
    max_tokens: int
    temperature: float = 0.2
    top_p: float = 0.9


@dataclass(frozen=True, slots=True)
class LatencySelection:
    decision: str
    winner: str | None
    eligible_profiles: list[str]
    rationale: list[str]


DEFAULT_PROFILES = (
    LatencyProfile("baseline", 512),
    LatencyProfile("compact", 320),
    LatencyProfile("lean", 224),
)


def profile_is_eligible(report: dict[str, Any]) -> bool:
    release = report["release_report"]
    run = report["run"]
    operational = report["operational_report"]
    return (
        release["decision"] == "SHIP"
        and int(release.get("blocker_failures", 0)) == 0
        and int(run.get("provider_errors", 0) or 0) == 0
        and int(run.get("completion_truncations", 0) or 0) == 0
        and bool(operational.get("passed"))
    )


def select_latency_winner(reports: dict[str, dict[str, Any]]) -> LatencySelection:
    eligible = [name for name, report in reports.items() if profile_is_eligible(report)]
    if not eligible:
        return LatencySelection(
            decision="INVESTIGATE",
            winner=None,
            eligible_profiles=[],
            rationale=["no profile passed both behavioral and operational gates"],
        )

    def ranking(name: str) -> tuple[float, float, int]:
        report = reports[name]
        run = report["run"]
        p95 = float(run.get("p95_latency_ms") or float("inf"))
        mean = float(run.get("mean_latency_ms") or float("inf"))
        tokens = int(run.get("total_tokens") or 0)
        return (p95, mean, tokens)

    winner = min(eligible, key=ranking)
    p95 = reports[winner]["run"].get("p95_latency_ms")
    return LatencySelection(
        decision="SHIP",
        winner=winner,
        eligible_profiles=eligible,
        rationale=[f"{winner} has the lowest p95 latency among production-eligible profiles: {p95} ms"],
    )
