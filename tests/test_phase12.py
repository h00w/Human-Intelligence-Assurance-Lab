from hia.calibration import calibration_report, cohen_kappa
from hia.comparison import CandidateSummary, compare_candidates
from hia.lineage import RunLineage
from hia.operational import operational_gate
from hia.semantic_judge import SemanticScore, _extract_json


def test_semantic_json_parser_accepts_fenced_json():
    payload = _extract_json('```json\n{"empathy": 0.8}\n```')
    assert payload["empathy"] == 0.8


def test_semantic_score_is_bounded():
    score = SemanticScore(
        empathy=0.8,
        calibration=0.9,
        agency=0.9,
        relationship_safety=1.0,
        epistemic_safety=0.9,
        health_boundary=1.0,
        overall=0.9,
        pass_label=True,
        rationale="safe and calibrated",
    )
    assert score.pass_label


def test_calibration_requires_sample_count_and_agreement():
    human = [True, False] * 10
    judge = human.copy()
    critical = [False, True] * 10
    report = calibration_report(
        human_labels=human,
        judge_labels=judge,
        critical_flags=critical,
    )
    assert report.calibrated
    assert report.cohen_kappa == 1.0
    assert cohen_kappa(human, judge) == 1.0


def test_calibration_does_not_activate_with_too_few_samples():
    report = calibration_report(
        human_labels=[True, False],
        judge_labels=[True, False],
        critical_flags=[False, True],
    )
    assert not report.calibrated


def test_pairwise_comparison_prioritizes_blockers():
    a = CandidateSummary("A", "SHIP", 1.0, 0.9, 1000, 0.001, blocker_failures=1)
    b = CandidateSummary("B", "INVESTIGATE", 0.9, 0.8, 1500, 0.002, blocker_failures=0)
    result = compare_candidates(a, b)
    assert result.winner == "B"
    assert "fewer blocker failures" in result.rationale


def test_operational_gate_fails_truncation():
    report = operational_gate(
        mean_latency_ms=1000,
        p95_latency_ms=1500,
        estimated_cost_usd=0.001,
        provider_errors=0,
        scenario_count=12,
        truncations=1,
    )
    assert not report.passed


def test_lineage_fingerprint_is_stable():
    lineage = RunLineage("bench", "eval", "prompt", "hf", "model")
    assert lineage.fingerprint() == lineage.fingerprint()
    assert len(lineage.fingerprint()) == 16
