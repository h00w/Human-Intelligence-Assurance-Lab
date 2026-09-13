from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class V1Readiness:
    status: str
    ready: bool
    phase18_ship: bool
    human_calibrated: bool
    long_window_ready: bool
    dedicated_status: str
    blockers: tuple[str, ...]


def assess_v1_readiness(
    *,
    phase18_ship: bool,
    human_calibrated: bool,
    long_window_ready: bool,
    dedicated_status: str,
) -> V1Readiness:
    blockers: list[str] = []
    hard_failure = False
    if not phase18_ship:
        blockers.append("authoritative Phase 1.8 production SHIP is required")
        hard_failure = True
    if not human_calibrated:
        blockers.append("independent human semantic calibration has not passed")
    if not long_window_ready:
        blockers.append("time-separated production qualification is incomplete")
    normalized = dedicated_status.upper()
    if normalized != "QUALIFIED":
        blockers.append("dedicated infrastructure has not been explicitly provisioned and qualified")
        if normalized == "HOLD":
            hard_failure = True
    ready = not blockers
    status = "READY" if ready else ("HOLD" if hard_failure else "BLOCKED")
    return V1Readiness(
        status=status,
        ready=ready,
        phase18_ship=phase18_ship,
        human_calibrated=human_calibrated,
        long_window_ready=long_window_ready,
        dedicated_status=normalized,
        blockers=tuple(blockers),
    )
