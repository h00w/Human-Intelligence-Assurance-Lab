from hia.v1_readiness import assess_v1_readiness


def test_v1_is_blocked_without_humans_time_or_dedicated():
    result = assess_v1_readiness(
        phase18_ship=True,
        human_calibrated=False,
        long_window_ready=False,
        dedicated_status="NOT_CONFIGURED",
    )
    assert result.status == "BLOCKED"
    assert result.ready is False
    assert len(result.blockers) == 3


def test_v1_ready_only_when_all_maturity_gates_pass():
    result = assess_v1_readiness(
        phase18_ship=True,
        human_calibrated=True,
        long_window_ready=True,
        dedicated_status="QUALIFIED",
    )
    assert result.status == "READY"
    assert result.ready is True


def test_v1_holds_on_failed_required_gate():
    result = assess_v1_readiness(
        phase18_ship=False,
        human_calibrated=True,
        long_window_ready=True,
        dedicated_status="QUALIFIED",
    )
    assert result.status == "HOLD"
