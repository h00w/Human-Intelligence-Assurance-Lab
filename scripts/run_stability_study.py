from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.runner import load_scenarios
from hia.stability import summarize_stability

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "stability_study_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def main() -> None:
    token = os.environ["HF_TOKEN"]
    model = os.getenv("HIA_STABILITY_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    provider = os.getenv("HIA_STABILITY_PROVIDER", "deepinfra")
    trials = int(os.getenv("HIA_STABILITY_TRIALS", "5"))
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    max_tokens = int(os.getenv("HIA_STABILITY_MAX_TOKENS", "512"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    reports: list[dict] = []
    for trial in range(1, trials + 1):
        adapter = HuggingFaceAdapter(
            model=model,
            provider=provider,
            token=token,
            max_tokens=max_tokens,
            temperature=0.2,
            top_p=0.9,
            input_price_per_million=None,
            output_price_per_million=None,
        )
        report = run_model_evaluation(
            adapter,
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )
        report["trial"] = trial
        reports.append(report)

    stability = summarize_stability(reports)
    payload = {
        "schema_version": "1.4",
        "purpose": "repeated-run production confidence",
        "model": model,
        "provider": provider,
        "trial_count": trials,
        "scenario_count_per_trial": len(scenarios),
        "generation": {
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "top_p": 0.9,
        },
        "constants": {
            "benchmark": True,
            "policy": "risk-aware",
            "model": True,
            "provider": True,
            "generation_parameters": True,
        },
        "stability": asdict(stability),
        "trials": reports,
        "interpretation": (
            "Phase 1.4 measures whether the Phase 1.3 production-SHIP result repeats under the same configuration. "
            "A single fast or safe run cannot compensate for instability across trials."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/stability_study_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(
        BUCKET,
        add=[(str(OUT), "runs/stability_study_latest.json")],
        token=token,
    )

    print(json.dumps(payload["stability"], indent=2))
    for report in reports:
        print(
            json.dumps(
                {
                    "trial": report["trial"],
                    "behavioral": report["release_report"]["decision"],
                    "production": report["production_decision"]["decision"],
                    "pass_rate": report["release_report"]["pass_rate"],
                    "blockers": report["release_report"]["blocker_failures"],
                    "provider_errors": report["run"]["provider_errors"],
                    "truncations": report["run"]["completion_truncations"],
                    "mean_latency_ms": report["run"]["mean_latency_ms"],
                    "p95_latency_ms": report["run"]["p95_latency_ms"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
