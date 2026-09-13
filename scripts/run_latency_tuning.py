from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.latency_tuning import DEFAULT_PROFILES, select_latency_winner
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.runner import load_scenarios

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "latency_tuning_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def main() -> None:
    token = os.environ["HF_TOKEN"]
    provider = os.getenv("HIA_LATENCY_PROVIDER", "deepinfra")
    model = os.getenv("HIA_LATENCY_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    reports: dict[str, dict] = {}
    for profile in DEFAULT_PROFILES:
        adapter = HuggingFaceAdapter(
            model=model,
            provider=provider,
            token=token,
            max_tokens=profile.max_tokens,
            temperature=profile.temperature,
            top_p=profile.top_p,
            input_price_per_million=None,
            output_price_per_million=None,
        )
        reports[profile.name] = run_model_evaluation(
            adapter,
            scenarios,
            system_prompt_builder=risk_aware_system_prompt,
        )

    selection = select_latency_winner(reports)
    payload = {
        "schema_version": "1.3",
        "purpose": "latency tuning under fixed risk-aware policy",
        "model": model,
        "provider": provider,
        "benchmark_constant": True,
        "policy_constant": True,
        "profiles": {
            profile.name: {
                "generation": {
                    "max_tokens": profile.max_tokens,
                    "temperature": profile.temperature,
                    "top_p": profile.top_p,
                },
                "report": reports[profile.name],
            }
            for profile in DEFAULT_PROFILES
        },
        "selection": {
            "decision": selection.decision,
            "winner": selection.winner,
            "eligible_profiles": selection.eligible_profiles,
            "rationale": selection.rationale,
        },
        "interpretation": (
            "A profile is production-eligible only if behavioral safety, completeness, and operational SLOs all pass. "
            "Latency optimization is never allowed to compensate for a safety regression."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/latency_tuning_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(
        BUCKET,
        add=[(str(OUT), "runs/latency_tuning_latest.json")],
        token=token,
    )

    print(json.dumps(payload["selection"], indent=2))
    for name, report in reports.items():
        print(
            json.dumps(
                {
                    "profile": name,
                    "production_decision": report["production_decision"],
                    "run": report["run"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
