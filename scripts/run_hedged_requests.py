from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.resilience import (
    FaultInjectingAdapter,
    HedgedAdapter,
    average_hedge_attempts,
    fallback_winner_rate,
    hedge_rate,
)
from hia.runner import load_scenarios
from hia.stability import summarize_stability

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "hedged_requests_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _adapter(*, model: str, provider: str, token: str, timeout_s: float = 4.0) -> HuggingFaceAdapter:
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


def _hedged(
    *,
    model: str,
    primary: str,
    fallback: str,
    token: str,
    hedge_delay_ms: float,
    primary_adapter=None,
    fallback_adapter=None,
) -> HedgedAdapter:
    return HedgedAdapter(
        primary_adapter or _adapter(model=model, provider=primary, token=token),
        fallback_adapter or _adapter(model=model, provider=fallback, token=token),
        hedge_delay_ms=hedge_delay_ms,
    )


def _summary(report: dict) -> dict:
    run = report["run"]
    release = report["release_report"]
    production = report["production_decision"]
    return {
        "behavioral": release["decision"],
        "production": production["decision"],
        "pass_rate": release["pass_rate"],
        "blockers": release["blocker_failures"],
        "provider_errors": run.get("provider_errors", 0),
        "truncations": run.get("completion_truncations", 0),
        "mean_latency_ms": run.get("mean_latency_ms"),
        "p95_latency_ms": run.get("p95_latency_ms"),
        "hedge_rate": round(hedge_rate(report), 4),
        "fallback_winner_rate": round(fallback_winner_rate(report), 4),
        "average_attempts": round(average_hedge_attempts(report), 4),
    }


def _eligible(report: dict) -> bool:
    summary = _summary(report)
    return (
        summary["behavioral"] == "SHIP"
        and summary["production"] == "SHIP"
        and summary["blockers"] == 0
        and summary["provider_errors"] == 0
        and summary["truncations"] == 0
        and summary["mean_latency_ms"] is not None
        and summary["mean_latency_ms"] <= 5000
        and summary["p95_latency_ms"] is not None
        and summary["p95_latency_ms"] <= 8000
    )


def main() -> None:
    token = os.environ["HF_TOKEN"]
    model = os.getenv("HIA_HEDGE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    primary = os.getenv("HIA_HEDGE_PRIMARY", "nscale")
    fallback = os.getenv("HIA_HEDGE_FALLBACK", "novita")
    thresholds = [
        float(value.strip())
        for value in os.getenv("HIA_HEDGE_THRESHOLDS_MS", "500,1000,1500,2000").split(",")
        if value.strip()
    ]
    repeated_trials = int(os.getenv("HIA_HEDGE_REPEATED_TRIALS", "10"))
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    threshold_reports: dict[str, dict] = {}
    for threshold in thresholds:
        report = run_model_evaluation(
            _hedged(
                model=model,
                primary=primary,
                fallback=fallback,
                token=token,
                hedge_delay_ms=threshold,
            ),
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )
        threshold_reports[str(int(threshold))] = report

    eligible_thresholds = [
        (threshold, threshold_reports[str(int(threshold))])
        for threshold in thresholds
        if _eligible(threshold_reports[str(int(threshold))])
    ]
    if eligible_thresholds:
        eligible_thresholds.sort(
            key=lambda item: (
                item[1]["run"].get("p95_latency_ms") or float("inf"),
                item[1]["run"].get("mean_latency_ms") or float("inf"),
                hedge_rate(item[1]),
            )
        )
        selected_threshold = eligible_thresholds[0][0]
        threshold_decision = "SHIP"
    else:
        selected_threshold = min(thresholds)
        threshold_decision = "HOLD"

    # The primary consumes its full four-second deadline, but the fallback launches
    # at the selected hedge threshold instead of waiting for the timeout.
    delayed_timeout_primary = FaultInjectingAdapter(
        _adapter(model=model, provider=primary, token=token),
        mode="timeout",
        latency_ms=4000.0,
        sleep_before_fault=True,
    )
    timeout_recovery = run_model_evaluation(
        _hedged(
            model=model,
            primary=primary,
            fallback=fallback,
            token=token,
            hedge_delay_ms=selected_threshold,
            primary_adapter=delayed_timeout_primary,
        ),
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )

    truncation_primary = FaultInjectingAdapter(
        _adapter(model=model, provider=primary, token=token),
        mode="truncation",
    )
    truncation_recovery = run_model_evaluation(
        _hedged(
            model=model,
            primary=primary,
            fallback=fallback,
            token=token,
            hedge_delay_ms=selected_threshold,
            primary_adapter=truncation_primary,
        ),
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )

    dual_failure = run_model_evaluation(
        _hedged(
            model=model,
            primary=primary,
            fallback=fallback,
            token=token,
            hedge_delay_ms=selected_threshold,
            primary_adapter=FaultInjectingAdapter(
                _adapter(model=model, provider=primary, token=token), mode="error"
            ),
            fallback_adapter=FaultInjectingAdapter(
                _adapter(model=model, provider=fallback, token=token), mode="error"
            ),
        ),
        scenarios[:2],
        system_prompt_builder=risk_aware_system_prompt,
    )

    repeated_reports: list[dict] = []
    for trial in range(1, repeated_trials + 1):
        report = run_model_evaluation(
            _hedged(
                model=model,
                primary=primary,
                fallback=fallback,
                token=token,
                hedge_delay_ms=selected_threshold,
            ),
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )
        report["trial"] = trial
        report["hedging"] = {
            "hedge_rate": round(hedge_rate(report), 4),
            "fallback_winner_rate": round(fallback_winner_rate(report), 4),
            "average_attempts": round(average_hedge_attempts(report), 4),
        }
        repeated_reports.append(report)
    stability = summarize_stability(repeated_reports, minimum_trials=repeated_trials)

    timeout_pass = _eligible(timeout_recovery) and fallback_winner_rate(timeout_recovery) > 0
    truncation_pass = _eligible(truncation_recovery) and fallback_winner_rate(truncation_recovery) > 0
    dual_holds = dual_failure["production_decision"]["decision"] == "HOLD"
    executive_ship = (
        threshold_decision == "SHIP"
        and timeout_pass
        and truncation_pass
        and dual_holds
        and stability.stable
    )

    dedicated_url = os.getenv("HIA_DEDICATED_ENDPOINT_URL")
    payload = {
        "schema_version": "1.7",
        "purpose": "hedged requests and dedicated infrastructure bakeoff",
        "model": model,
        "routes": {"primary": primary, "fallback": fallback},
        "release_contract": {
            "behavioral": "SHIP",
            "blockers": 0,
            "unrecovered_truncations": 0,
            "final_provider_errors": 0,
            "max_mean_latency_ms": 5000,
            "max_p95_latency_ms": 8000,
        },
        "threshold_bakeoff": {
            "candidates_ms": thresholds,
            "selected_ms": selected_threshold,
            "decision": threshold_decision,
            "reports": {
                key: {"summary": _summary(report), "report": report}
                for key, report in threshold_reports.items()
            },
        },
        "fault_recovery": {
            "primary_timeout": {
                "summary": _summary(timeout_recovery),
                "passed": timeout_pass,
                "report": timeout_recovery,
            },
            "primary_truncation": {
                "summary": _summary(truncation_recovery),
                "passed": truncation_pass,
                "report": truncation_recovery,
            },
            "simultaneous_degradation": {
                "summary": _summary(dual_failure),
                "failed_closed": dual_holds,
                "report": dual_failure,
            },
        },
        "extended_qualification": {
            "trial_count": repeated_trials,
            "scenario_count_per_trial": len(scenarios),
            "stability": asdict(stability),
            "trials": repeated_reports,
        },
        "infrastructure_bakeoff": {
            "routed_hedged": {
                "status": "MEASURED",
                "primary": primary,
                "fallback": fallback,
                "selected_hedge_delay_ms": selected_threshold,
                "stability": asdict(stability),
            },
            "dedicated": {
                "status": "NOT_CONFIGURED" if not dedicated_url else "CONFIGURED_NOT_EXECUTED",
                "endpoint_url_present": bool(dedicated_url),
                "release_critical": False,
                "reason": (
                    "No dedicated endpoint was explicitly provisioned. HIA-Lab does not silently create paid infrastructure."
                    if not dedicated_url
                    else "Endpoint URL is present; a provider-specific authenticated adapter is required before a fair bakeoff."
                ),
            },
        },
        "executive_decision": {
            "decision": "SHIP" if executive_ship else "HOLD",
            "reasons": [
                f"hedge threshold bakeoff: {threshold_decision}",
                "timeout recovery passed" if timeout_pass else "timeout recovery failed",
                "truncation recovery passed" if truncation_pass else "truncation recovery failed",
                "simultaneous degradation failed closed" if dual_holds else "dual degradation did not fail closed",
                "extended qualification passed" if stability.stable else "extended qualification failed",
            ],
            "dedicated_infrastructure_release_critical": False,
        },
        "interpretation": (
            "Hedging measures user-visible decision latency to the first complete response while retaining loser provenance. "
            "The qualification harness waits for in-flight losers only to record evidence; that wait is not charged to decision latency."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/hedged_requests_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(BUCKET, add=[(str(OUT), "runs/hedged_requests_latest.json")], token=token)

    print(
        json.dumps(
            {
                "selected_hedge_delay_ms": selected_threshold,
                "threshold_decision": threshold_decision,
                "timeout_recovery": _summary(timeout_recovery),
                "truncation_recovery": _summary(truncation_recovery),
                "dual_failure_holds": dual_holds,
                "extended_stable": stability.stable,
                "worst_trial_p95_ms": stability.worst_trial_p95_ms,
                "decision": payload["executive_decision"]["decision"],
                "dedicated": payload["infrastructure_bakeoff"]["dedicated"]["status"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
