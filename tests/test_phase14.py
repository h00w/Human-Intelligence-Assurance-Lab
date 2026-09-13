from hia.executive_assurance import executive_assurance_decision
from hia.stability import summarize_stability


def _trial(*, production="SHIP", behavioral="SHIP", blockers=0, errors=0, truncations=0, mean_ms=3500, p95_ms=6500):
    return {
        "production_decision": {"decision": production},
        "release_report": {"decision": behavioral, "blocker_failures": blockers},
        "run": {
            "provider_errors": errors,
            "completion_truncations": truncations,
            "mean_latency_ms": mean_ms,
            "p95_latency_ms": p95_ms,
        },
    }


def test_repeated_clean_trials_are_stable():
    report = summarize_stability([_trial(p95_ms=6200 + i * 100) for i in range(5)])
    assert report.stable is True
    assert report.production_ship_rate == 1.0
    assert report.blocker_trial_rate == 0.0
    assert report.worst_trial_p95_ms == 6600
    assert report.mean_latency_ci95 is not None


def test_single_blocker_trial_breaks_stability():
    trials = [_trial() for _ in range(5)]
    trials[2] = _trial(production="HOLD", behavioral="HOLD", blockers=1)
    report = summarize_stability(trials)
    assert report.stable is False
    assert report.blocker_trial_rate == 0.2
    assert any("blocker trial rate" in reason for reason in report.reasons)


def test_worst_p95_above_slo_breaks_stability():
    trials = [_trial() for _ in range(4)] + [_trial(p95_ms=9000, production="INVESTIGATE")]
    report = summarize_stability(trials)
    assert report.stable is False
    assert any("worst trial p95" in reason for reason in report.reasons)


def test_executive_manifest_can_ship_with_semantic_shadow():
    decision = executive_assurance_decision(
        stability={"stable": True, "reasons": []},
        calibration=None,
        require_semantic_calibration=False,
    )
    assert decision.decision == "SHIP"
    assert any("shadow-only" in reason for reason in decision.reasons)


def test_release_critical_semantic_requires_calibration():
    decision = executive_assurance_decision(
        stability={"stable": True, "reasons": []},
        calibration={"report": {"calibrated": False}},
        require_semantic_calibration=True,
    )
    assert decision.decision == "HOLD"
