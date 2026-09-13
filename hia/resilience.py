from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean

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


class FailoverAdapter(ModelAdapter):
    """Try ordered provider adapters, failing over on timeout/error/truncation.

    The adapter preserves total end-to-end latency across attempts. A fallback can
    recover availability/completeness, but it cannot hide time already spent on a
    failed primary route.
    """

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
                        "provider": result.metadata.get("routing_provider", adapter.provider),
                        "latency_ms": result.latency_ms,
                        "finish_reason": finish_reason,
                        "status": "truncated" if finish_reason == "length" else "success",
                    }
                )
                if finish_reason != "length":
                    metadata = dict(result.metadata)
                    metadata.update(
                        {
                            "failover_attempts": attempts,
                            "selected_provider": result.metadata.get(
                                "routing_provider", adapter.provider
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
                attempts.append(
                    {
                        "attempt": index + 1,
                        "provider": getattr(adapter, "routing_provider", adapter.provider),
                        "status": "error",
                        "error_type": type(exc).__name__,
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
