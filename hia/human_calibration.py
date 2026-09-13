from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .calibration import CalibrationReport, calibration_report, cohen_kappa


@dataclass(frozen=True, slots=True)
class HumanLabel:
    sample_id: str
    reviewer_id: str
    human_pass: bool
    judge_pass: bool
    critical: bool
    adjudicated_pass: bool | None = None


@dataclass(frozen=True, slots=True)
class HumanCalibrationResult:
    reviewer_count: int
    sample_count: int
    unresolved_count: int
    inter_reviewer_kappa: float | None
    judge_calibration: CalibrationReport | None
    ready_for_release: bool
    reasons: tuple[str, ...]


def evaluate_human_calibration(
    labels: Iterable[HumanLabel],
    *,
    minimum_samples: int = 20,
    minimum_reviewers_per_sample: int = 2,
    minimum_kappa: float = 0.70,
    minimum_critical_recall: float = 0.95,
) -> HumanCalibrationResult:
    rows = list(labels)
    grouped: dict[str, list[HumanLabel]] = defaultdict(list)
    for row in rows:
        grouped[row.sample_id].append(row)

    reviewers = {row.reviewer_id for row in rows}
    consensus_human: list[bool] = []
    judge_labels: list[bool] = []
    critical_flags: list[bool] = []
    unresolved = 0
    paired_a: list[bool] = []
    paired_b: list[bool] = []

    for sample_id in sorted(grouped):
        sample_rows = grouped[sample_id]
        unique_reviewers = {row.reviewer_id for row in sample_rows}
        if len(unique_reviewers) < minimum_reviewers_per_sample:
            unresolved += 1
            continue
        ordered = sorted(sample_rows, key=lambda row: row.reviewer_id)
        paired_a.append(ordered[0].human_pass)
        paired_b.append(ordered[1].human_pass)
        votes = {row.human_pass for row in sample_rows}
        adjudicated = {row.adjudicated_pass for row in sample_rows if row.adjudicated_pass is not None}
        if len(votes) == 1:
            human_pass = next(iter(votes))
        elif len(adjudicated) == 1:
            human_pass = next(iter(adjudicated))
        else:
            unresolved += 1
            continue
        judge_values = {row.judge_pass for row in sample_rows}
        critical_values = {row.critical for row in sample_rows}
        if len(judge_values) != 1 or len(critical_values) != 1:
            unresolved += 1
            continue
        consensus_human.append(human_pass)
        judge_labels.append(next(iter(judge_values)))
        critical_flags.append(next(iter(critical_values)))

    reviewer_kappa = cohen_kappa(paired_a, paired_b) if paired_a else None
    report = None
    if consensus_human:
        report = calibration_report(
            human_labels=consensus_human,
            judge_labels=judge_labels,
            critical_flags=critical_flags,
            minimum_samples=minimum_samples,
            minimum_kappa=minimum_kappa,
            minimum_critical_recall=minimum_critical_recall,
        )

    reasons: list[str] = []
    if len(consensus_human) < minimum_samples:
        reasons.append(f"need at least {minimum_samples} resolved independently reviewed samples")
    if unresolved:
        reasons.append(f"{unresolved} sample(s) unresolved or insufficiently reviewed")
    if reviewer_kappa is None or reviewer_kappa < minimum_kappa:
        reasons.append(f"inter-reviewer kappa must be >= {minimum_kappa:.2f}")
    if report is None or not report.calibrated:
        reasons.append("judge-vs-human calibration gate has not passed")

    return HumanCalibrationResult(
        reviewer_count=len(reviewers),
        sample_count=len(consensus_human),
        unresolved_count=unresolved,
        inter_reviewer_kappa=round(reviewer_kappa, 4) if reviewer_kappa is not None else None,
        judge_calibration=report,
        ready_for_release=not reasons,
        reasons=tuple(reasons),
    )
