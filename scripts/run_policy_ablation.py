from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.comparison import CandidateSummary, compare_candidates
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.runner import load_scenarios

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "policy_ablation_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _summary(name: str, report: dict) -> CandidateSummary:
    release = report["release_report"]
    run = report["run"]
    return CandidateSummary(
        name=name,
        decision=release["decision"],
        pass_rate=release["pass_rate"],
        semantic_score=None,
        mean_latency_ms=run.get("mean_latency_ms"),
        estimated_cost_usd=run.get("estimated_cost_usd"),
        blocker_failures=release["blocker_failures"],
    )


def _adapter(model: str, provider: str, token: str) -> HuggingFaceAdapter:
    return HuggingFaceAdapter(
        model=model,
        provider=provider,
        token=token,
        max_tokens=512,
        temperature=0.2,
        top_p=0.9,
        input_price_per_million=None,
        output_price_per_million=None,
    )


def main() -> None:
    token = os.environ["HF_TOKEN"]
    provider = os.getenv("HIA_POLICY_PROVIDER", "deepinfra")
    model = os.getenv("HIA_POLICY_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    generic = run_model_evaluation(_adapter(model, provider, token), scenarios)
    risk_aware = run_model_evaluation(
        _adapter(model, provider, token),
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )
    comparison = compare_candidates(
        _summary("generic_policy", generic),
        _summary("risk_aware_policy", risk_aware),
    )

    payload = {
        "schema_version": "1.2.2",
        "purpose": "policy injection ablation",
        "model": model,
        "provider": provider,
        "benchmark_constant": True,
        "generation_parameters_constant": True,
        "generic_policy": generic,
        "risk_aware_policy": risk_aware,
        "comparison": {
            "winner": comparison.winner,
            "rationale": comparison.rationale,
        },
        "interpretation": (
            "This isolates the effect of executable risk-aware prompt policy while keeping model, provider, "
            "benchmark, and generation parameters constant."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/policy_ablation_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(
        BUCKET,
        add=[(str(OUT), "runs/policy_ablation_latest.json")],
        token=token,
    )

    print(json.dumps(payload["comparison"], indent=2))
    print(json.dumps({"generic": generic["release_report"], "risk_aware": risk_aware["release_report"]}, indent=2))
    print(json.dumps({"generic": generic["run"], "risk_aware": risk_aware["run"]}, indent=2))


if __name__ == "__main__":
    main()
