from hia.production_gate import production_decision


def _release(decision: str = "SHIP") -> dict:
    return {"decision": decision}


def _operational(passed: bool = True, reasons: list[str] | None = None) -> dict:
    return {"passed": passed, "reasons": reasons or []}


def _run(provider_errors: int = 0, truncations: int = 0) -> dict:
    return {
        "provider_errors": provider_errors,
        "completion_truncations": truncations,
    }


def test_behavioral_hold_forces_production_hold():
    result = production_decision(
        release_report=_release("HOLD"),
        operational_report=_operational(),
        run=_run(),
    )
    assert result.decision == "HOLD"


def test_provider_error_forces_hold_even_if_behavioral_ship():
    result = production_decision(
        release_report=_release("SHIP"),
        operational_report=_operational(False, ["provider errors: 1"]),
        run=_run(provider_errors=1),
    )
    assert result.decision == "HOLD"
    assert "provider errors=1" in result.reasons[0]


def test_truncation_forces_hold_even_if_behavioral_ship():
    result = production_decision(
        release_report=_release("SHIP"),
        operational_report=_operational(False, ["completion truncations: 1"]),
        run=_run(truncations=1),
    )
    assert result.decision == "HOLD"


def test_latency_regression_requires_investigation():
    result = production_decision(
        release_report=_release("SHIP"),
        operational_report=_operational(False, ["p95 latency exceeds threshold"]),
        run=_run(),
    )
    assert result.decision == "INVESTIGATE"
    assert "operational: p95 latency exceeds threshold" in result.reasons


def test_behavioral_investigate_cannot_production_ship():
    result = production_decision(
        release_report=_release("INVESTIGATE"),
        operational_report=_operational(),
        run=_run(),
    )
    assert result.decision == "INVESTIGATE"


def test_ship_requires_behavioral_and_operational_pass():
    result = production_decision(
        release_report=_release("SHIP"),
        operational_report=_operational(),
        run=_run(),
    )
    assert result.decision == "SHIP"


def test_uncalibrated_release_critical_semantic_gate_holds():
    result = production_decision(
        release_report=_release("SHIP"),
        operational_report=_operational(),
        run=_run(),
        semantic_release_critical=True,
        semantic_calibrated=False,
        semantic_passed=True,
    )
    assert result.decision == "HOLD"
