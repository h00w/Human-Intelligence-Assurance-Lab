from __future__ import annotations

import pytest

from hia.adapters.base import GenerationResult, ModelAdapter
from hia.resilience import (
    FailoverAdapter,
    FaultInjectedError,
    FaultInjectingAdapter,
    select_provider,
)


class FakeAdapter(ModelAdapter):
    def __init__(
        self,
        provider: str,
        *,
        fail: bool = False,
        truncate: bool = False,
        latency_ms: float = 10.0,
    ):
        self.provider = provider
        self.model = "fake-model"
        self.fail = fail
        self.truncate = truncate
        self.latency_ms = latency_ms
        self.routing_provider = provider

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        if self.fail:
            raise TimeoutError(f"{self.provider} timed out")
        return GenerationResult(
            provider="huggingface",
            model=self.model,
            text="Safe concise answer.",
            latency_ms=self.latency_ms,
            metadata={
                "routing_provider": self.provider,
                "finish_reason": "length" if self.truncate else "stop",
            },
        )


def _report(
    *,
    decision="SHIP",
    behavioral="SHIP",
    p95=5000.0,
    blockers=0,
    errors=0,
    truncations=0,
):
    return {
        "production_decision": {"decision": decision},
        "release_report": {
            "decision": behavioral,
            "pass_rate": 1.0,
            "blocker_failures": blockers,
        },
        "run": {
            "provider_errors": errors,
            "completion_truncations": truncations,
            "mean_latency_ms": p95 / 2,
            "p95_latency_ms": p95,
        },
    }


def test_provider_selection_prefers_lowest_eligible_p95():
    reports = {
        "slow": _report(p95=7000.0),
        "fast": _report(p95=4500.0),
        "unsafe": _report(p95=2000.0, blockers=1, behavioral="HOLD", decision="HOLD"),
    }
    selection = select_provider(reports)
    assert selection.winner == "fast"
    assert selection.eligible == ["fast", "slow"]


def test_provider_selection_does_not_trade_safety_for_speed():
    reports = {
        "fast-unsafe": _report(
            p95=1000.0,
            blockers=1,
            behavioral="HOLD",
            decision="HOLD",
        )
    }
    selection = select_provider(reports)
    assert selection.winner is None
    assert selection.eligible == []


def test_failover_recovers_from_primary_timeout_and_preserves_attempts():
    adapter = FailoverAdapter(
        [FakeAdapter("primary", fail=True), FakeAdapter("fallback", latency_ms=20.0)]
    )
    result = adapter.generate(system_prompt="system", user_prompt="user")
    assert result.text == "Safe concise answer."
    assert result.metadata["failover_used"] is True
    assert result.metadata["selected_provider"] == "fallback"
    assert len(result.metadata["failover_attempts"]) == 2


def test_failover_recovers_from_truncation_and_keeps_total_latency():
    adapter = FailoverAdapter(
        [
            FakeAdapter("primary", truncate=True, latency_ms=30.0),
            FakeAdapter("fallback", latency_ms=20.0),
        ]
    )
    result = adapter.generate(system_prompt="system", user_prompt="user")
    assert result.metadata["selected_provider"] == "fallback"
    assert result.latency_ms == 50.0
    assert result.metadata["failover_attempts"][0]["status"] == "truncated"


def test_fault_injected_timeout_charges_deadline_before_fallback():
    primary = FaultInjectingAdapter(
        FakeAdapter("primary"),
        mode="timeout",
        latency_ms=4000.0,
    )
    fallback = FaultInjectingAdapter(FakeAdapter("fallback", latency_ms=25.0), mode="none")
    result = FailoverAdapter([primary, fallback]).generate(system_prompt="system", user_prompt="user")
    assert result.metadata["failover_used"] is True
    assert result.metadata["selected_provider"] == "fallback"
    assert result.metadata["failover_attempts"][0]["fault_injected"] is True
    assert result.metadata["failover_attempts"][0]["latency_ms"] == 4000.0
    assert result.latency_ms == 4025.0


def test_fault_injected_truncation_is_recovered_by_fallback():
    primary = FaultInjectingAdapter(FakeAdapter("primary", latency_ms=15.0), mode="truncation")
    fallback = FaultInjectingAdapter(FakeAdapter("fallback", latency_ms=20.0), mode="none")
    result = FailoverAdapter([primary, fallback]).generate(system_prompt="system", user_prompt="user")
    assert result.latency_ms == 35.0
    assert result.metadata["failover_attempts"][0]["status"] == "truncated"
    assert result.metadata["selected_provider"] == "fallback"


def test_simultaneous_injected_provider_errors_fail_closed():
    primary = FaultInjectingAdapter(FakeAdapter("primary"), mode="error")
    fallback = FaultInjectingAdapter(FakeAdapter("fallback"), mode="error")
    with pytest.raises(FaultInjectedError):
        FailoverAdapter([primary, fallback]).generate(system_prompt="system", user_prompt="user")
