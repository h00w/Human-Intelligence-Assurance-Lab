from __future__ import annotations

import time
from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, TimeoutError as FutureTimeout, wait
from dataclasses import dataclass
from statistics import mean
from typing import Any

from .adapters.base import GenerationResult, ModelAdapter


@dataclass(slots=True)
class ProviderCandidate:
    provider: str
    decision: str
    behavioral_decision: str
    pass_rate: float
    blocker_failures: int
    provider_errors: int
    truncations: int
    mean_latency_ms: float | None
    p95_latency_ms: float | None


@dataclass(slots=True)
class ProviderSelection:
    winner: str | None
    eligible: list[str]
    rationale: list[str]


def provider_candidate(provider: str, report: dict) -> ProviderCandidate:
    run = report["run"]
    release = report["release_report"]
    production = report["production_decision"]
    return ProviderCandidate(
        provider=provider,
        decision=production["decision"],
        behavioral_decision=release["decision"],
        pass_rate=release["pass_rate"],
        blocker_failures=release["blocker_failures"],
        provider_errors=run.get("provider_errors", 0),
        truncations=run.get("completion_truncations", 0),
        mean_latency_ms=run.get("mean_latency_ms"),
        p95_latency_ms=run.get("p95_latency_ms"),
    )


def select_provider(reports: dict[str, dict], *, p95_slo_ms: float = 8000.0) -> ProviderSelection:
    candidates = [provider_candidate(provider, report) for provider, report in reports.items()]
    eligible = [
        candidate
        for candidate in candidates
        if candidate.behavioral_decision == "SHIP"
        and candidate.blocker_failures == 0
        and candidate.provider_errors == 0
        and candidate.truncations == 0
        and candidate.p95_latency_ms is not None
        and candidate.p95_latency_ms <= p95_slo_ms
    ]
    eligible.sort(
        key=lambda item: (
            item.p95_latency_ms or float("inf"),
            item.mean_latency_ms or float("inf"),
        )
    )
    if not eligible:
        return ProviderSelection(
            winner=None,
            eligible=[],
            rationale=["no provider route satisfied behavioral, completeness, and p95 SLO gates"],
        )
    winner = eligible[0]
    return ProviderSelection(
        winner=winner.provider,
        eligible=[item.provider for item in eligible],
        rationale=[
            f"{winner.provider} had the lowest eligible p95 latency ({winner.p95_latency_ms:.0f} ms)",
            "safety/completeness gates dominate latency optimization",
        ],
    )


class FaultInjectedError(RuntimeError):
    """Explicit synthetic infrastructure fault used only by qualification experiments."""


class FaultInjectedTimeout(TimeoutError):
    """Synthetic timeout carrying the consumed deadline budget as evidence."""

    def __init__(self, message: str, *, latency_ms: float) -> None:
        super().__init__(message)
        self.latency_ms = latency_ms


class FaultInjectingAdapter(ModelAdapter):
    """Wrap a real adapter and deterministically inject timeout/error/truncation faults.

    Faults are labeled so injected failures cannot be confused with naturally occurring
    provider failures. ``sleep_before_fault`` is reserved for wall-clock resilience tests:
    it makes an injected timeout consume its configured budget before raising.
    """

    def __init__(
        self,
        adapter: ModelAdapter,
        *,
        mode: str = "none",
        latency_ms: float = 0.0,
        sleep_before_fault: bool = False,
    ) -> None:
        if mode not in {"none", "timeout", "error", "truncation"}:
            raise ValueError(f"unsupported fault mode: {mode}")
        self.adapter = adapter
        self.mode = mode
        self.injected_latency_ms = latency_ms
        self.sleep_before_fault = sleep_before_fault
        self.provider = getattr(adapter, "provider", "fault-injection")
        self.routing_provider = getattr(adapter, "routing_provider", self.provider)
        self.model = adapter.model

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        if self.mode == "timeout":
            if self.sleep_before_fault and self.injected_latency_ms > 0:
                time.sleep(self.injected_latency_ms / 1000)
            raise FaultInjectedTimeout(
                f"injected timeout for {self.routing_provider}",
                latency_ms=self.injected_latency_ms,
            )
        if self.mode == "error":
            raise FaultInjectedError(f"injected provider error for {self.routing_provider}")

        result = self.adapter.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        if self.mode != "truncation":
            return result

        metadata = dict(result.metadata)
        metadata.update(
            {"finish_reason": "length", "fault_injected": True, "fault_mode": "truncation"}
        )
        return GenerationResult(
            provider=result.provider,
            model=result.model,
            text=result.text,
            latency_ms=round(result.latency_ms + self.injected_latency_ms, 2),
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            estimated_cost_usd=result.estimated_cost_usd,
            metadata=metadata,
        )


class FailoverAdapter(ModelAdapter):
    """Try ordered provider adapters, failing over on timeout/error/truncation."""

    provider = "failover"

    def __init__(self, adapters: Iterable[ModelAdapter]) -> None:
        self.adapters = list(adapters)
        if not self.adapters:
            raise ValueError("at least one adapter is required")
        self.model = self.adapters[0].model

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        attempts: list[dict] = []
        total_latency_ms = 0.0
        last_result: GenerationResult | None = None
        last_error: Exception | None = None

        for index, adapter in enumerate(self.adapters):
            try:
                result = adapter.generate(system_prompt=system_prompt, user_prompt=user_prompt)
                total_latency_ms += result.latency_ms
                last_result = result
                finish_reason = result.metadata.get("finish_reason")
                attempts.append(
                    {
                        "attempt": index + 1,
                        "provider": result.metadata.get(
                            "routing_provider", getattr(adapter, "routing_provider", adapter.provider)
                        ),
                        "latency_ms": result.latency_ms,
                        "finish_reason": finish_reason,
                        "status": "truncated" if finish_reason == "length" else "success",
                        "fault_injected": bool(result.metadata.get("fault_injected")),
                    }
                )
                if finish_reason != "length":
                    metadata = dict(result.metadata)
                    metadata.update(
                        {
                            "failover_attempts": attempts,
                            "selected_provider": result.metadata.get(
                                "routing_provider", getattr(adapter, "routing_provider", adapter.provider)
                            ),
                            "failover_used": index > 0,
                        }
                    )
                    return GenerationResult(
                        provider=self.provider,
                        model=result.model,
                        text=result.text,
                        latency_ms=round(total_latency_ms, 2),
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                        total_tokens=result.total_tokens,
                        estimated_cost_usd=result.estimated_cost_usd,
                        metadata=metadata,
                    )
            except Exception as exc:  # noqa: BLE001 - provider boundary must fail over
                last_error = exc
                failure_latency_ms = float(getattr(exc, "latency_ms", 0.0) or 0.0)
                total_latency_ms += failure_latency_ms
                attempts.append(
                    {
                        "attempt": index + 1,
                        "provider": getattr(adapter, "routing_provider", adapter.provider),
                        "latency_ms": failure_latency_ms,
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "fault_injected": isinstance(
                            exc, (FaultInjectedError, FaultInjectedTimeout)
                        ),
                    }
                )

        if last_result is not None:
            metadata = dict(last_result.metadata)
            metadata.update(
                {
                    "failover_attempts": attempts,
                    "selected_provider": last_result.metadata.get(
                        "routing_provider", last_result.provider
                    ),
                    "failover_used": len(attempts) > 1,
                }
            )
            return GenerationResult(
                provider=self.provider,
                model=last_result.model,
                text=last_result.text,
                latency_ms=round(total_latency_ms, 2),
                prompt_tokens=last_result.prompt_tokens,
                completion_tokens=last_result.completion_tokens,
                total_tokens=last_result.total_tokens,
                estimated_cost_usd=last_result.estimated_cost_usd,
                metadata=metadata,
            )

        if last_error is not None:
            raise last_error
        raise RuntimeError("failover adapter exhausted without a result")


@dataclass(slots=True)
class _HedgeOutcome:
    role: str
    provider: str
    launched_at_ms: float
    completed_at_ms: float
    result: GenerationResult | None = None
    error: Exception | None = None


class HedgedAdapter(ModelAdapter):
    """Launch fallback before the primary deadline and use the first complete response.

    Decision latency is wall-clock time until the first non-truncated response. During
    qualification, any already-running losing request is allowed to finish so its token,
    cost, completion, and provider evidence can be recorded. This wait is *not* charged
    to user-visible decision latency. A production transport may cancel the loser when
    its provider/client supports cancellation; otherwise it can safely ignore the result.
    """

    provider = "hedged"

    def __init__(
        self,
        primary: ModelAdapter,
        fallback: ModelAdapter,
        *,
        hedge_delay_ms: float = 1000.0,
    ) -> None:
        if hedge_delay_ms < 0:
            raise ValueError("hedge_delay_ms must be non-negative")
        self.primary = primary
        self.fallback = fallback
        self.hedge_delay_ms = hedge_delay_ms
        self.model = primary.model

    @staticmethod
    def _provider_name(adapter: ModelAdapter) -> str:
        return str(getattr(adapter, "routing_provider", adapter.provider))

    @staticmethod
    def _complete(result: GenerationResult) -> bool:
        return result.metadata.get("finish_reason") != "length" and bool(result.text.strip())

    def _invoke(
        self,
        *,
        role: str,
        adapter: ModelAdapter,
        overall_started: float,
        system_prompt: str,
        user_prompt: str,
    ) -> _HedgeOutcome:
        launched_at_ms = (time.perf_counter() - overall_started) * 1000
        try:
            result = adapter.generate(system_prompt=system_prompt, user_prompt=user_prompt)
            return _HedgeOutcome(
                role=role,
                provider=self._provider_name(adapter),
                launched_at_ms=launched_at_ms,
                completed_at_ms=(time.perf_counter() - overall_started) * 1000,
                result=result,
            )
        except Exception as exc:  # noqa: BLE001 - provider boundary evidence
            return _HedgeOutcome(
                role=role,
                provider=self._provider_name(adapter),
                launched_at_ms=launched_at_ms,
                completed_at_ms=(time.perf_counter() - overall_started) * 1000,
                error=exc,
            )

    @staticmethod
    def _record(outcome: _HedgeOutcome, *, decision_latency_ms: float | None) -> dict[str, Any]:
        if outcome.result is not None:
            finish_reason = outcome.result.metadata.get("finish_reason")
            return {
                "role": outcome.role,
                "provider": outcome.result.metadata.get("routing_provider", outcome.provider),
                "launched_at_ms": round(outcome.launched_at_ms, 2),
                "completed_at_ms": round(outcome.completed_at_ms, 2),
                "provider_latency_ms": outcome.result.latency_ms,
                "status": "truncated" if finish_reason == "length" else "success",
                "finish_reason": finish_reason,
                "prompt_tokens": outcome.result.prompt_tokens,
                "completion_tokens": outcome.result.completion_tokens,
                "total_tokens": outcome.result.total_tokens,
                "estimated_cost_usd": outcome.result.estimated_cost_usd,
                "fault_injected": bool(outcome.result.metadata.get("fault_injected")),
                "completed_after_decision": (
                    decision_latency_ms is not None and outcome.completed_at_ms > decision_latency_ms
                ),
            }
        error = outcome.error
        return {
            "role": outcome.role,
            "provider": outcome.provider,
            "launched_at_ms": round(outcome.launched_at_ms, 2),
            "completed_at_ms": round(outcome.completed_at_ms, 2),
            "provider_latency_ms": float(getattr(error, "latency_ms", 0.0) or 0.0),
            "status": "error",
            "error_type": type(error).__name__ if error is not None else "UnknownError",
            "fault_injected": isinstance(error, (FaultInjectedError, FaultInjectedTimeout)),
            "completed_after_decision": (
                decision_latency_ms is not None and outcome.completed_at_ms > decision_latency_ms
            ),
        }

    def _build_result(
        self,
        *,
        winner: _HedgeOutcome,
        outcomes: list[_HedgeOutcome],
        decision_latency_ms: float,
        fallback_launched: bool,
    ) -> GenerationResult:
        assert winner.result is not None
        attempts = [
            self._record(outcome, decision_latency_ms=decision_latency_ms)
            for outcome in sorted(outcomes, key=lambda item: item.launched_at_ms)
        ]
        observed_tokens = [
            outcome.result.total_tokens
            for outcome in outcomes
            if outcome.result is not None and outcome.result.total_tokens is not None
        ]
        observed_costs = [
            outcome.result.estimated_cost_usd
            for outcome in outcomes
            if outcome.result is not None and outcome.result.estimated_cost_usd is not None
        ]
        metadata = dict(winner.result.metadata)
        metadata.update(
            {
                "hedge_used": fallback_launched,
                "hedge_delay_ms": self.hedge_delay_ms,
                "hedge_attempts": attempts,
                "selected_provider": winner.result.metadata.get(
                    "routing_provider", winner.provider
                ),
                "winning_role": winner.role,
                "decision_latency_ms": round(decision_latency_ms, 2),
                "observed_total_tokens": sum(observed_tokens) if observed_tokens else None,
                "observed_estimated_cost_usd": round(sum(observed_costs), 8)
                if observed_costs
                else None,
                "loser_policy": (
                    "qualification waits for in-flight loser to finish for provenance; "
                    "production may cancel when transport supports cancellation or ignore it"
                ),
            }
        )
        return GenerationResult(
            provider=self.provider,
            model=winner.result.model,
            text=winner.result.text,
            latency_ms=round(decision_latency_ms, 2),
            prompt_tokens=winner.result.prompt_tokens,
            completion_tokens=winner.result.completion_tokens,
            total_tokens=winner.result.total_tokens,
            estimated_cost_usd=winner.result.estimated_cost_usd,
            metadata=metadata,
        )

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        overall_started = time.perf_counter()
        outcomes: list[_HedgeOutcome] = []
        winner: _HedgeOutcome | None = None
        decision_latency_ms: float | None = None
        fallback_launched = False

        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="hia-hedge") as executor:
            primary_future = executor.submit(
                self._invoke,
                role="primary",
                adapter=self.primary,
                overall_started=overall_started,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            futures: dict[Future[_HedgeOutcome], str] = {primary_future: "primary"}

            try:
                early = primary_future.result(timeout=self.hedge_delay_ms / 1000)
                outcomes.append(early)
                if early.result is not None and self._complete(early.result):
                    winner = early
                    decision_latency_ms = early.completed_at_ms
                else:
                    fallback_launched = True
            except FutureTimeout:
                fallback_launched = True

            if winner is None and fallback_launched:
                fallback_future = executor.submit(
                    self._invoke,
                    role="fallback",
                    adapter=self.fallback,
                    overall_started=overall_started,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                futures[fallback_future] = "fallback"

                already_recorded = {id(early)} if "early" in locals() else set()
                pending = {future for future in futures if not future.done()}
                for future in futures:
                    if future.done():
                        outcome = future.result()
                        if id(outcome) not in already_recorded:
                            outcomes.append(outcome)

                while pending and winner is None:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        outcome = future.result()
                        outcomes.append(outcome)
                        if outcome.result is not None and self._complete(outcome.result):
                            winner = outcome
                            decision_latency_ms = outcome.completed_at_ms
                            break

                if pending:
                    done, _ = wait(pending)
                    for future in done:
                        outcomes.append(future.result())

            if winner is not None and decision_latency_ms is not None:
                return self._build_result(
                    winner=winner,
                    outcomes=outcomes,
                    decision_latency_ms=decision_latency_ms,
                    fallback_launched=fallback_launched,
                )

        truncated = [item for item in outcomes if item.result is not None]
        if truncated:
            last = max(truncated, key=lambda item: item.completed_at_ms)
            assert last.result is not None
            metadata = dict(last.result.metadata)
            metadata.update(
                {
                    "hedge_used": fallback_launched,
                    "hedge_delay_ms": self.hedge_delay_ms,
                    "hedge_attempts": [
                        self._record(item, decision_latency_ms=None) for item in outcomes
                    ],
                    "selected_provider": last.provider,
                    "winning_role": None,
                    "decision_latency_ms": round(last.completed_at_ms, 2),
                }
            )
            return GenerationResult(
                provider=self.provider,
                model=last.result.model,
                text=last.result.text,
                latency_ms=round(last.completed_at_ms, 2),
                prompt_tokens=last.result.prompt_tokens,
                completion_tokens=last.result.completion_tokens,
                total_tokens=last.result.total_tokens,
                estimated_cost_usd=last.result.estimated_cost_usd,
                metadata=metadata,
            )

        errors = [item.error for item in outcomes if item.error is not None]
        if errors:
            raise errors[-1]
        raise RuntimeError("hedged adapter exhausted without response evidence")


def failover_rate(report: dict) -> float:
    evidence = report.get("evidence", [])
    if not evidence:
        return 0.0
    used = 0
    for row in evidence:
        if row.get("generation", {}).get("metadata", {}).get("failover_used"):
            used += 1
    return used / len(evidence)


def average_attempts(report: dict) -> float:
    values = []
    for row in report.get("evidence", []):
        attempts = row.get("generation", {}).get("metadata", {}).get("failover_attempts", [])
        if attempts:
            values.append(len(attempts))
    return mean(values) if values else 0.0


def hedge_rate(report: dict) -> float:
    evidence = report.get("evidence", [])
    if not evidence:
        return 0.0
    used = sum(
        1
        for row in evidence
        if row.get("generation", {}).get("metadata", {}).get("hedge_used")
    )
    return used / len(evidence)


def fallback_winner_rate(report: dict) -> float:
    evidence = report.get("evidence", [])
    if not evidence:
        return 0.0
    wins = sum(
        1
        for row in evidence
        if row.get("generation", {}).get("metadata", {}).get("winning_role") == "fallback"
    )
    return wins / len(evidence)


def average_hedge_attempts(report: dict) -> float:
    counts = []
    for row in report.get("evidence", []):
        attempts = row.get("generation", {}).get("metadata", {}).get("hedge_attempts", [])
        if attempts:
            counts.append(len(attempts))
    return mean(counts) if counts else 0.0
