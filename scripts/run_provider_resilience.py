from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.resilience import FailoverAdapter, average_attempts, failover_rate, provider_candidate, select_provider
from hia.runner import load_scenarios
from hia.stability import summarize_stability

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "provider_resilience_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _adapter(*, model: str, provider: str, token: str, timeout_s: float) -> HuggingFaceAdapter:
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


def main() -> None:
    token = os.environ["HF_TOKEN"]
    model = os.getenv("HIA_RESILIENCE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    providers = [p.strip() for p in os.getenv("HIA_RESILIENCE_PROVIDERS", "novita,nscale,deepinfra").split(",") if p.strip()]
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    trials = int(os.getenv("HIA_RESILIENCE_TRIALS", "5"))
    bakeoff_timeout_s = float(os.getenv("HIA_BAKEOFF_TIMEOUT_S", "8"))
    primary_timeout_s = float(os.getenv("HIA_PRIMARY_TIMEOUT_S", "4"))
    fallback_timeout_s = float(os.getenv("HIA_FALLBACK_TIMEOUT_S", "4"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    # Stage A: same model + policy + benchmark across provider routes.
    provider_reports: dict[str, dict] = {}
    for provider in providers:
        provider_reports[provider] = run_model_evaluation(
            _adapter(model=model, provider=provider, token=token, timeout_s=bakeoff_timeout_s),
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )

    selection = select_provider(provider_reports)
    candidates = [provider_candidate(provider, report) for provider, report in provider_reports.items()]

    # Build a safe-first route order. If no provider satisfies the p95 SLO in the
    # bakeoff, keep the fastest complete behavioral-SHIP routes for remediation evidence.
    safe_candidates = [
        c
        for c in candidates
        if c.behavioral_decision == "SHIP"
        and c.blocker_failures == 0
        and c.provider_errors == 0
        and c.truncations == 0
        and c.p95_latency_ms is not None
    ]
    safe_candidates.sort(key=lambda c: (c.p95_latency_ms or float("inf"), c.mean_latency_ms or float("inf")))
    route_order = [c.provider for c in safe_candidates]
    if not route_order:
        route_order = providers[:]
    route_order = route_order[:2]

    # Stage B: hard timeout + fallback. Total end-to-end latency remains visible;
    # fallback is not allowed to erase time consumed by the primary attempt.
    repeated_reports: list[dict] = []
    for trial in range(1, trials + 1):
        adapters = []
        for index, provider in enumerate(route_order):
            timeout_s = primary_timeout_s if index == 0 else fallback_timeout_s
            adapters.append(_adapter(model=model, provider=provider, token=token, timeout_s=timeout_s))
        report = run_model_evaluation(
            FailoverAdapter(adapters),
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )
        report["trial"] = trial
        report["resilience"] = {
            "route_order": route_order,
            "failover_rate": round(failover_rate(report), 4),
            "average_attempts": round(average_attempts(report), 4),
        }
        repeated_reports.append(report)

    stability = summarize_stability(repeated_reports)
    executive_decision = "SHIP" if stability.stable else "HOLD"
    payload = {
        "schema_version": "1.5",
        "purpose": "provider resilience and bounded critical-response qualification",
        "model": model,
        "provider_bakeoff": {
            "providers": providers,
            "request_timeout_s": bakeoff_timeout_s,
            "reports": provider_reports,
            "selection": asdict(selection),
        },
        "bounded_policy": {
            "critical_front_load": True,
            "critical_target_words": 120,
            "critical_wellness_no_speculative_differential": True,
        },
        "failover": {
            "route_order": route_order,
            "primary_timeout_s": primary_timeout_s,
            "fallback_timeout_s": fallback_timeout_s,
            "note": "end-to-end latency includes every attempted route; fallback cannot hide primary-route delay",
        },
        "qualification": {
            "trial_count": trials,
            "scenario_count_per_trial": len(scenarios),
            "stability": asdict(stability),
            "trials": repeated_reports,
        },
        "executive_decision": {
            "decision": executive_decision,
            "reasons": stability.reasons,
        },
        "interpretation": (
            "Phase 1.5 changes routing resilience and critical-response control while retaining the Phase 1.4 "
            "release thresholds. Provider speed cannot compensate for a blocker, truncation, or incomplete evidence."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/provider_resilience_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(BUCKET, add=[(str(OUT), "runs/provider_resilience_latest.json")], token=token)

    print(json.dumps(payload["provider_bakeoff"]["selection"], indent=2))
    print(json.dumps(payload["failover"], indent=2))
    print(json.dumps(payload["qualification"]["stability"], indent=2))
    print(json.dumps(payload["executive_decision"], indent=2))


if __name__ == "__main__":
    main()
