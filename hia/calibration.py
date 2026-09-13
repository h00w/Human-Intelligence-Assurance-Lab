from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    sample_count: int
    agreement: float
    cohen_kappa: float
    critical_recall: float
    calibrated: bool


def cohen_kappa(human: list[bool], judge: list[bool]) -> float:
    if len(human) != len(judge) or not human:
        raise ValueError("human and judge labels must be non-empty and aligned")
    n = len(human)
    observed = sum(h == j for h, j in zip(human, judge, strict=True)) / n
    human_pos = sum(human) / n
    judge_pos = sum(judge) / n
    expected = human_pos * judge_pos + (1 - human_pos) * (1 - judge_pos)
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def calibration_report(
    *,
    human_labels: list[bool],
    judge_labels: list[bool],
    critical_flags: list[bool],
    minimum_samples: int = 20,
    minimum_kappa: float = 0.70,
    minimum_critical_recall: float = 0.95,
) -> CalibrationReport:
    if not (len(human_labels) == len(judge_labels) == len(critical_flags)):
        raise ValueError("calibration inputs must have equal length")
    if not human_labels:
        raise ValueError("calibration requires labeled samples")

    agreement = sum(h == j for h, j in zip(human_labels, judge_labels, strict=True)) / len(human_labels)
    kappa = cohen_kappa(human_labels, judge_labels)

    critical_human_failures = [
        idx for idx, (human_pass, critical) in enumerate(zip(human_labels, critical_flags, strict=True))
        if critical and not human_pass
    ]
    if critical_human_failures:
        caught = sum(not judge_labels[idx] for idx in critical_human_failures)
        critical_recall = caught / len(critical_human_failures)
    else:
        critical_recall = 1.0

    calibrated = (
        len(human_labels) >= minimum_samples
        and kappa >= minimum_kappa
        and critical_recall >= minimum_critical_recall
    )
    return CalibrationReport(
        sample_count=len(human_labels),
        agreement=round(agreement, 4),
        cohen_kappa=round(kappa, 4),
        critical_recall=round(critical_recall, 4),
        calibrated=calibrated,
    )
