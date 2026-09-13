from __future__ import annotations

import time

import pytest

from hia.adapters.base import GenerationResult, ModelAdapter
from hia.resilience import HedgedAdapter


class SleepAdapter(ModelAdapter):
    def __init__(
        self,
        provider: str,
        *,
        sleep_ms: float,
        truncate: bool = False,
        fail: bool = False,
    ) -> None:
        self.provider = provider
        self.routing_provider = provider
        self.model = "fake-model"
        self.sleep_ms = sleep_ms
        self.truncate = truncate
        self.fail = fail

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        time.sleep(self.sleep_ms / 1000)
        if self.fail:
            raise RuntimeError(f"{self.provider} failed")
        return GenerationResult(
            provider=self.provider,
            model=self.model,
            text="complete answer",
            latency_ms=self.sleep_ms,
            total_tokens=10,
            metadata={
                "routing_provider": self.provider,
                "finish_reason": "length" if self.truncate else "stop",
            },
        )


def test_fast_primary_does_not_launch_hedge():
    result = HedgedAdapter(
        SleepAdapter("primary", sleep_ms=5),
        SleepAdapter("fallback", sleep_ms=5),
        hedge_delay_ms=50,
    ).generate(system_prompt="s", user_prompt="u")
    assert result.metadata["hedge_used"] is False
    assert result.metadata["winning_role"] == "primary"
    assert len(result.metadata["hedge_attempts"]) == 1


def test_slow_primary_lets_fallback_win_before_primary_finishes():
    result = HedgedAdapter(
        SleepAdapter("primary", sleep_ms=80),
        SleepAdapter("fallback", sleep_ms=15),
        hedge_delay_ms=20,
    ).generate(system_prompt="s", user_prompt="u")
    assert result.metadata["hedge_used"] is True
    assert result.metadata["winning_role"] == "fallback"
    assert result.metadata["selected_provider"] == "fallback"
    assert result.latency_ms < 70
    assert len(result.metadata["hedge_attempts"]) == 2
    assert any(a["completed_after_decision"] for a in result.metadata["hedge_attempts"])


def test_truncated_primary_cannot_win():
    result = HedgedAdapter(
        SleepAdapter("primary", sleep_ms=5, truncate=True),
        SleepAdapter("fallback", sleep_ms=10),
        hedge_delay_ms=50,
    ).generate(system_prompt="s", user_prompt="u")
    assert result.metadata["winning_role"] == "fallback"
    assert result.metadata["hedge_used"] is True


def test_both_routes_error_fail_closed():
    adapter = HedgedAdapter(
        SleepAdapter("primary", sleep_ms=1, fail=True),
        SleepAdapter("fallback", sleep_ms=1, fail=True),
        hedge_delay_ms=5,
    )
    with pytest.raises(RuntimeError):
        adapter.generate(system_prompt="s", user_prompt="u")
