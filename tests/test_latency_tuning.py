from hia.latency_tuning import profile_is_eligible, select_latency_winner


def _report(*, decision="SHIP", blockers=0, errors=0, truncations=0, operational=True, p95=7000, mean=3000, tokens=1000):
    return {
        "release_report": {"decision": decision, "blocker_failures": blockers},
        "run": {
            "provider_errors": errors,
            "completion_truncations": truncations,
            "p95_latency_ms": p95,
            "mean_latency_ms": mean,
            "total_tokens": tokens,
        },
        "operational_report": {"passed": operational, "reasons": []},
    }


def test_profile_requires_behavioral_and_operational_pass():
    assert profile_is_eligible(_report())
    assert not profile_is_eligible(_report(decision="HOLD"))
    assert not profile_is_eligible(_report(blockers=1))
    assert not profile_is_eligible(_report(errors=1))
    assert not profile_is_eligible(_report(truncations=1))
    assert not profile_is_eligible(_report(operational=False))


def test_lowest_p95_eligible_profile_wins():
    reports = {
        "baseline": _report(p95=7600, mean=4200, tokens=1800),
        "compact": _report(p95=5200, mean=3000, tokens=1300),
        "lean": _report(p95=6100, mean=2500, tokens=900),
    }
    result = select_latency_winner(reports)
    assert result.decision == "SHIP"
    assert result.winner == "compact"
    assert set(result.eligible_profiles) == {"baseline", "compact", "lean"}


def test_no_eligible_profile_requires_investigation():
    reports = {
        "baseline": _report(operational=False),
        "compact": _report(truncations=1),
        "lean": _report(decision="HOLD", blockers=1),
    }
    result = select_latency_winner(reports)
    assert result.decision == "INVESTIGATE"
    assert result.winner is None
