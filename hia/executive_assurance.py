from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutiveAssuranceDecision:
    decision: str
    reasons: list[str]


def executive_assurance_decision(
    *,
    stability: dict[str, Any] | None,
    calibration: dict[str, Any] | None,
    require_semantic_calibration: bool = False,
) -> ExecutiveAssuranceDecision:
    reasons: list[str] = []

    if not stability:
        return ExecutiveAssuranceDecision("HOLD", ["missing repeated-run stability evidence"])
    if not bool(stability.get("stable")):
        reasons.extend(stability.get("reasons") or ["repeated-run stability contract failed"])
        return ExecutiveAssuranceDecision("HOLD", reasons)

    if require_semantic_calibration:
        if not calibration:
            return ExecutiveAssuranceDecision("HOLD", ["semantic calibration is required but no report is available"])
        report = calibration.get("report", calibration)
        if not bool(report.get("calibrated")):
            return ExecutiveAssuranceDecision("HOLD", ["semantic calibration contract has not passed"])
        return ExecutiveAssuranceDecision(
            "SHIP",
            ["repeated-run stability and release-critical semantic calibration passed"],
        )

    if calibration:
        report = calibration.get("report", calibration)
        if bool(report.get("calibrated")):
            reasons.append("semantic judge is independently calibrated and eligible for promotion")
        else:
            reasons.append("semantic calibration remains pending; semantic judge stays shadow-only")
    else:
        reasons.append("semantic calibration not yet published; semantic judge stays shadow-only")

    return ExecutiveAssuranceDecision(
        "SHIP",
        ["repeated-run production-confidence contract passed", *reasons],
    )
