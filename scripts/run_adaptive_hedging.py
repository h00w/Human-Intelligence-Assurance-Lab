from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.adaptive import AdaptiveHedgePolicy, AdaptiveHedgedAdapter, cohort_metrics, routing_economics
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.resilience import FaultInjectingAdapter, HedgedAdapter
from hia.runner import load_scenarios
from hia.stability import summarize_stability

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "adaptive_hedging_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"
PRICING = {
    "nscale": {"input": 0.06, "output": 0.06},
    "novita": {"input": 0.02, "output": 0.05},
}


def adapter(model: str, provider: str, token: str, timeout_s: float = 4.0):
    price = PRICING[provider]
    return HuggingFaceAdapter(
        model=model,
        provider=provider,
        token=token,
        max_tokens=512,
        temperature=0.2,
        top_p=0.9,
        timeout_s=timeout_s,
        input_price_per_million=price["input"],
        output_price_per_million=price["output"],
    )


def balanced_risk_sample(scenarios, per_risk: int = 6):
    out = []
    for risk in ("critical", "high", "medium", "low"):
        selected = [s for s in scenarios if s.risk_level == risk][:per_risk]
        out.extend(selected)
    return out


def latencies(report: dict) -> list[float]:
    return [
        float(row["generation"]["latency_ms"])
        for row in report["evidence"]
        if row.get("error") is None
    ]


def eligible(report: dict) -> bool:
    run = report["run"]
    release = report["release_report"]
    production = report["production_decision"]
    return (
        release["decision"] == "SHIP"
        and production["decision"] == "SHIP"
        and release["blocker_failures"] == 0
        and run["provider_errors"] == 0
        and run["completion_truncations"] == 0
        and (run["mean_latency_ms"] or 999999) <= 5000
        and (run["p95_latency_ms"] or 999999) <= 8000
    )


def main() -> None:
    token = os.environ["HF_TOKEN"]
    model = os.getenv("HIA_ADAPTIVE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    primary = os.getenv("HIA_ADAPTIVE_PRIMARY", "nscale")
    fallback = os.getenv("HIA_ADAPTIVE_FALLBACK", "novita")
    repeated_trials = int(os.getenv("HIA_ADAPTIVE_TRIALS", "5"))
    all_scenarios = load_scenarios()
    eval_scenarios = balanced_risk_sample(all_scenarios, per_risk=6)
    calibration_scenarios = select_canary(all_scenarios, per_domain=2)
    risk_by_prompt = {s.input.user_message: s.risk_level for s in all_scenarios}

    # Measure the current primary route first. The adaptive schedule is derived only from
    # this run's latency distribution, then frozen for all comparison/qualification runs.
    calibration = run_model_evaluation(
        adapter(model, primary, token),
        calibration_scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )
    policy = AdaptiveHedgePolicy.from_latencies(latencies(calibration))

    adaptive = AdaptiveHedgedAdapter(
        adapter(model, primary, token),
        adapter(model, fallback, token),
        policy=policy,
        risk_by_prompt=risk_by_prompt,
    )
    adaptive_report = run_model_evaluation(
        adaptive, eval_scenarios, system_prompt_builder=risk_aware_system_prompt
    )

    fixed_report = run_model_evaluation(
        HedgedAdapter(
            adapter(model, primary, token),
            adapter(model, fallback, token),
            hedge_delay_ms=1500,
        ),
        eval_scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )

    # Critical-path fault recovery uses the risk-derived critical delay.
    critical_cases = [s for s in eval_scenarios if s.risk_level == "critical"]
    timeout_primary = FaultInjectingAdapter(
        adapter(model, primary, token), mode="timeout", latency_ms=4000, sleep_before_fault=True
    )
    timeout_report = run_model_evaluation(
        AdaptiveHedgedAdapter(
            timeout_primary,
            adapter(model, fallback, token),
            policy=policy,
            risk_by_prompt=risk_by_prompt,
        ),
        critical_cases,
        system_prompt_builder=risk_aware_system_prompt,
    )

    repeated = []
    for trial in range(1, repeated_trials + 1):
        report = run_model_evaluation(
            AdaptiveHedgedAdapter(
                adapter(model, primary, token),
                adapter(model, fallback, token),
                policy=policy,
                risk_by_prompt=risk_by_prompt,
            ),
            eval_scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )
        report["trial"] = trial
        report["economics"] = routing_economics(report)
        repeated.append(report)
    stability = summarize_stability(repeated, minimum_trials=repeated_trials)

    adaptive_econ = routing_economics(adaptive_report)
    fixed_econ = routing_economics(fixed_report)
    cohorts = cohort_metrics(adaptive_report)
    timeout_econ = routing_economics(timeout_report)
    cost_improved = (
        adaptive_econ["redundant_cost_usd"] is not None
        and fixed_econ["redundant_cost_usd"] is not None
        and adaptive_econ["redundant_cost_usd"] <= fixed_econ["redundant_cost_usd"]
    )
    executive_ship = eligible(adaptive_report) and eligible(timeout_report) and stability.stable

    payload = {
        "schema_version": "1.8",
        "purpose": "adaptive hedging and cost-aware routing",
        "model": model,
        "routes": {"primary": primary, "fallback": fallback},
        "pricing_snapshot": {
            "date": "2026-09-13",
            "source": "Hugging Face Inference Providers catalog",
            "usd_per_million_tokens": PRICING,
        },
        "release_contract": {
            "behavioral": "SHIP",
            "blockers": 0,
            "unrecovered_truncations": 0,
            "final_provider_errors": 0,
            "max_mean_latency_ms": 5000,
            "max_p95_latency_ms": 8000,
        },
        "calibration": {
            "scenario_count": calibration["run"]["scenario_count"],
            "latency_profile": asdict(policy.latency),
            "derived_delays_ms": policy.delays_ms,
            "report": calibration,
        },
        "comparison": {
            "adaptive": {
                "report": adaptive_report,
                "economics": adaptive_econ,
                "cohorts": cohorts,
            },
            "fixed_1500ms": {
                "report": fixed_report,
                "economics": fixed_econ,
            },
            "adaptive_redundant_cost_not_worse": cost_improved,
        },
        "critical_fault_recovery": {
            "fault": "primary timeout 4000 ms",
            "critical_delay_ms": policy.delay_for("critical"),
            "report": timeout_report,
            "economics": timeout_econ,
            "passed": eligible(timeout_report),
        },
        "repeated_qualification": {
            "trial_count": repeated_trials,
            "scenario_count_per_trial": len(eval_scenarios),
            "stability": asdict(stability),
            "trials": repeated,
        },
        "infrastructure": {
            "routed_adaptive": "MEASURED",
            "dedicated": "NOT_CONFIGURED",
            "dedicated_release_critical": False,
        },
        "executive_decision": {
            "decision": "SHIP" if executive_ship else "HOLD",
            "reasons": [
                "adaptive route passed" if eligible(adaptive_report) else "adaptive route failed",
                "critical timeout recovery passed" if eligible(timeout_report) else "critical timeout recovery failed",
                "repeated qualification passed" if stability.stable else "repeated qualification failed",
                (
                    "adaptive redundant cost <= fixed 1.5 s"
                    if cost_improved
                    else "adaptive redundant cost exceeded fixed 1.5 s; reported as efficiency evidence, not a safety override"
                ),
            ],
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/adaptive_hedging_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(BUCKET, add=[(str(OUT), "runs/adaptive_hedging_latest.json")], token=token)

    print(json.dumps({
        "derived_delays_ms": policy.delays_ms,
        "adaptive": {"production": adaptive_report["production_decision"]["decision"], **adaptive_econ},
        "fixed": {"production": fixed_report["production_decision"]["decision"], **fixed_econ},
        "critical_timeout": {
            "production": timeout_report["production_decision"]["decision"],
            "mean_latency_ms": timeout_report["run"]["mean_latency_ms"],
            "p95_latency_ms": timeout_report["run"]["p95_latency_ms"],
        },
        "stable": stability.stable,
        "decision": payload["executive_decision"]["decision"],
    }, indent=2))


if __name__ == "__main__":
    main()
