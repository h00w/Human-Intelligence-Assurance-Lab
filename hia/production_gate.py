from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProductionDecision:
    decision: str
    behavioral_decision: str
    operational_passed: bool
    semantic_release_critical: bool
    semantic_calibrated: bool | None
    reasons: list[str]


def production_decision(
    *,
    release_report: dict[str, Any],
    operational_report: dict[str, Any],
    run: dict[str, Any],
    semantic_release_critical: bool = False,
    semantic_calibrated: bool | None = None,
    semantic_passed: bool | None = None,
) -> ProductionDecision:
    behavioral = str(release_report["decision"])
    reasons: list[str] = []

    if behavioral == "HOLD":
        reasons.append("behavioral safety gate returned HOLD")
        return ProductionDecision(
            decision="HOLD",
            behavioral_decision=behavioral,
            operational_passed=bool(operational_report["passed"]),
            semantic_release_critical=semantic_release_critical,
            semantic_calibrated=semantic_calibrated,
            reasons=reasons,
        )

    provider_errors = int(run.get("provider_errors", 0) or 0)
    truncations = int(run.get("completion_truncations", 0) or 0)
    if provider_errors:
        reasons.append(f"incomplete evidence: provider errors={provider_errors}")
    if truncations:
        reasons.append(f"incomplete evidence: truncations={truncations}")
    if reasons:
        return ProductionDecision(
            decision="HOLD",
            behavioral_decision=behavioral,
            operational_passed=False,
            semantic_release_critical=semantic_release_critical,
            semantic_calibrated=semantic_calibrated,
            reasons=reasons,
        )

    if semantic_release_critical:
        if semantic_calibrated is not True:
            reasons.append("semantic judge is release-critical but not calibrated")
            return ProductionDecision(
                decision="HOLD",
                behavioral_decision=behavioral,
                operational_passed=bool(operational_report["passed"]),
                semantic_release_critical=True,
                semantic_calibrated=semantic_calibrated,
                reasons=reasons,
            )
        if semantic_passed is not True:
            reasons.append("calibrated semantic gate did not pass")
            return ProductionDecision(
                decision="HOLD",
                behavioral_decision=behavioral,
                operational_passed=bool(operational_report["passed"]),
                semantic_release_critical=True,
                semantic_calibrated=True,
                reasons=reasons,
            )

    if behavioral == "INVESTIGATE":
        reasons.append("behavioral quality thresholds require investigation")

    if not operational_report["passed"]:
        reasons.extend(f"operational: {reason}" for reason in operational_report.get("reasons", []))

    if reasons:
        return ProductionDecision(
            decision="INVESTIGATE",
            behavioral_decision=behavioral,
            operational_passed=False,
            semantic_release_critical=semantic_release_critical,
            semantic_calibrated=semantic_calibrated,
            reasons=reasons,
        )

    return ProductionDecision(
        decision="SHIP",
        behavioral_decision=behavioral,
        operational_passed=True,
        semantic_release_critical=semantic_release_critical,
        semantic_calibrated=semantic_calibrated,
        reasons=["behavioral and operational production gates passed"],
    )
