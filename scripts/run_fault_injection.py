from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.resilience import FailoverAdapter, FaultInjectingAdapter, average_attempts, failover_rate
from hia.runner import load_scenarios
from hia.stability import summarize_stability

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "fault_injection_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _real_adapter(*, model: str, provider: str, token: str, timeout_s: float = 4.0) -> HuggingFaceAdapter:
    return HuggingFaceAdapter(
        model=model,
        provider=provider,
        token=token,
        max_tokens=512,
        temperature=0.2,
        top_p=0.9,
        timeout_s=timeout_s,
        input_price_per_million=None,
        output_price_per_million=None,
    )


def _run_fault_case(
    *,
    name: str,
    primary_mode: str,
    fallback_mode: str,
    model: str,
    primary: str,
    fallback: str,
    token: str,
    scenarios: list,
) -> dict:
    primary_adapter = FaultInjectingAdapter(
        _real_adapter(model=model, provider=primary, token=token), mode=primary_mode
    )
    fallback_adapter = FaultInjectingAdapter(
        _real_adapter(model=model, provider=fallback, token=token), mode=fallback_mode
    )
    report = run_model_evaluation(
        FailoverAdapter([primary_adapter, fallback_adapter]),
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )
    return {
        "name": name,
        "primary_fault": primary_mode,
        "fallback_fault": fallback_mode,
        "failover_rate": round(failover_rate(report), 4),
        "average_attempts": round(average_attempts(report), 4),
        "report": report,
    }


def _fault_recovered(case: dict) -> bool:
    report = case["report"]
    return (
        report["release_report"]["decision"] == "SHIP"
        and report["production_decision"]["decision"] == "SHIP"
        and report["release_report"]["blocker_failures"] == 0
        and report["run"]["provider_errors"] == 0
        and report["run"]["completion_truncations"] == 0
        and case["failover_rate"] == 1.0
    )


def main() -> None:
    token = os.environ["HF_TOKEN"]
    model = os.getenv("HIA_FAULT_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    primary = os.getenv("HIA_FAULT_PRIMARY", "nscale")
    fallback = os.getenv("HIA_FAULT_FALLBACK", "novita")
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    repeated_trials = int(os.getenv("HIA_FAULT_REPEATED_TRIALS", "10"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    # Live fault injection: primary is deliberately broken while fallback remains a real route.
    timeout_case = _run_fault_case(
        name="primary_timeout_recovery",
        primary_mode="timeout",
        fallback_mode="none",
        model=model,
        primary=primary,
        fallback=fallback,
        token=token,
        scenarios=scenarios,
    )
    truncation_case = _run_fault_case(
        name="primary_truncation_recovery",
        primary_mode="truncation",
        fallback_mode="none",
        model=model,
        primary=primary,
        fallback=fallback,
        token=token,
        scenarios=scenarios,
    )

    # Simultaneous degradation must fail closed. Use a compact 2-case slice to avoid
    # wasting remote inference because both routes are deterministically faulted.
    degraded_scenarios = scenarios[:2]
    dual_failure_case = _run_fault_case(
        name="simultaneous_provider_degradation",
        primary_mode="error",
        fallback_mode="error",
        model=model,
        primary=primary,
        fallback=fallback,
        token=token,
        scenarios=degraded_scenarios,
    )
    dual_failure_holds = dual_failure_case["report"]["production_decision"]["decision"] == "HOLD"

    # Larger observation window: 10 repeated real runs with healthy primary/fallback.
    repeated_reports: list[dict] = []
    for trial in range(1, repeated_trials + 1):
        report = run_model_evaluation(
            FailoverAdapter(
                [
                    _real_adapter(model=model, provider=primary, token=token),
                    _real_adapter(model=model, provider=fallback, token=token),
                ]
            ),
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )
        report["trial"] = trial
        report["resilience"] = {
            "failover_rate": round(failover_rate(report), 4),
            "average_attempts": round(average_attempts(report), 4),
        }
        repeated_reports.append(report)
    stability = summarize_stability(repeated_reports, minimum_trials=repeated_trials)

    # Dedicated infrastructure comparison is executable only when a dedicated endpoint
    # has been provisioned explicitly. Phase 1.6 does not silently incur paid endpoint cost.
    dedicated_url = os.getenv("HIA_DEDICATED_ENDPOINT_URL")
    infrastructure_comparison = {
        "routed": {
            "primary": primary,
            "fallback": fallback,
            "model": model,
            "qualification": "measured",
            "stability": stability.__dict__ if hasattr(stability, "__dict__") else None,
        },
        "dedicated": {
            "status": "NOT_CONFIGURED" if not dedicated_url else "CONFIGURED_NOT_EXECUTED",
            "endpoint_url_present": bool(dedicated_url),
            "reason": (
                "No dedicated endpoint URL was provided; provisioning paid infrastructure is intentionally "
                "not performed implicitly. The comparison contract is ready for an explicitly provisioned endpoint."
                if not dedicated_url
                else "Dedicated endpoint URL is present; provider-specific authentication adapter is required before execution."
            ),
        },
    }

    recovery_pass = _fault_recovered(timeout_case) and _fault_recovered(truncation_case)
    executive_ship = recovery_pass and dual_failure_holds and stability.stable
    payload = {
        "schema_version": "1.6",
        "purpose": "fault injection and infrastructure qualification",
        "model": model,
        "routes": {"primary": primary, "fallback": fallback},
        "fault_injection": {
            "primary_timeout": timeout_case,
            "primary_truncation": truncation_case,
            "simultaneous_degradation": dual_failure_case,
            "recovery_contract_passed": recovery_pass,
            "dual_failure_failed_closed": dual_failure_holds,
        },
        "extended_qualification": {
            "trial_count": repeated_trials,
            "scenario_count_per_trial": len(scenarios),
            "stability": {
                "trials": stability.trials,
                "production_ship_rate": stability.production_ship_rate,
                "behavioral_ship_rate": stability.behavioral_ship_rate,
                "blocker_trial_rate": stability.blocker_trial_rate,
                "provider_error_trial_rate": stability.provider_error_trial_rate,
                "truncation_trial_rate": stability.truncation_trial_rate,
                "mean_latency_ms": stability.mean_latency_ms,
                "median_trial_p95_ms": stability.median_trial_p95_ms,
                "worst_trial_p95_ms": stability.worst_trial_p95_ms,
                "stable": stability.stable,
                "reasons": stability.reasons,
            },
            "trials": repeated_reports,
        },
        "infrastructure_comparison": infrastructure_comparison,
        "executive_decision": {
            "decision": "SHIP" if executive_ship else "HOLD",
            "reasons": [
                "timeout fallback recovery passed" if _fault_recovered(timeout_case) else "timeout fallback recovery failed",
                "truncation fallback recovery passed" if _fault_recovered(truncation_case) else "truncation fallback recovery failed",
                "simultaneous provider degradation failed closed" if dual_failure_holds else "dual degradation did not fail closed",
                "extended repeated qualification passed" if stability.stable else "extended repeated qualification failed",
            ],
            "dedicated_infrastructure_release_critical": False,
        },
        "interpretation": (
            "Injected faults are explicitly labeled and are used to exercise the real fallback route. "
            "Natural provider failures remain separately observable. Dedicated-endpoint comparison is non-release-critical "
            "until an endpoint is explicitly provisioned."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/fault_injection_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(BUCKET, add=[(str(OUT), "runs/fault_injection_latest.json")], token=token)

    print(json.dumps({
        "timeout_recovered": _fault_recovered(timeout_case),
        "truncation_recovered": _fault_recovered(truncation_case),
        "dual_failure_holds": dual_failure_holds,
        "extended_stable": stability.stable,
        "worst_trial_p95_ms": stability.worst_trial_p95_ms,
        "decision": payload["executive_decision"]["decision"],
        "dedicated": infrastructure_comparison["dedicated"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
