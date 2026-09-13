from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.comparison import CandidateSummary, compare_candidates
from hia.model_eval import run_model_evaluation, select_canary
from hia.runner import load_scenarios

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "model_bakeoff_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _summary(report: dict) -> CandidateSummary:
    release = report["release_report"]
    run = report["run"]
    return CandidateSummary(
        name=run["model"],
        decision=release["decision"],
        pass_rate=release["pass_rate"],
        semantic_score=None,
        mean_latency_ms=run.get("mean_latency_ms"),
        estimated_cost_usd=run.get("estimated_cost_usd"),
        blocker_failures=release["blocker_failures"],
    )


def main() -> None:
    token = os.environ["HF_TOKEN"]
    provider = os.getenv("HIA_BAKEOFF_PROVIDER", "deepinfra")
    baseline_model = os.getenv("HIA_BASELINE_MODEL", "ibm-granite/granite-4.2-3b")
    candidate_model = os.getenv("HIA_CANDIDATE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)

    baseline = HuggingFaceAdapter(
        model=baseline_model,
        provider=provider,
        token=token,
        max_tokens=1024,
        temperature=1.0,
        top_p=0.95,
        input_price_per_million=None,
        output_price_per_million=None,
    )
    candidate = HuggingFaceAdapter(
        model=candidate_model,
        provider=provider,
        token=token,
        max_tokens=512,
        temperature=0.2,
        top_p=0.9,
        input_price_per_million=None,
        output_price_per_million=None,
    )

    baseline_report = run_model_evaluation(baseline, scenarios)
    candidate_report = run_model_evaluation(candidate, scenarios)
    comparison = compare_candidates(_summary(baseline_report), _summary(candidate_report))

    payload = {
        "schema_version": "1.2.1",
        "purpose": "live candidate bakeoff",
        "comparison_policy": "safety-first lexicographic",
        "baseline": baseline_report,
        "candidate": candidate_report,
        "comparison": {
            "winner": comparison.winner,
            "rationale": comparison.rationale,
            "semantic_score_used": False,
        },
        "disclaimer": (
            "This comparison is specific to the HIA-Bench canary and current provider/model configurations. "
            "Semantic judge scores are not used until human calibration requirements are satisfied."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/model_bakeoff_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(
        BUCKET,
        add=[(str(OUT), "runs/model_bakeoff_latest.json")],
        token=token,
    )

    print(json.dumps(payload["comparison"], indent=2))
    print(json.dumps({"baseline": baseline_report["run"], "candidate": candidate_report["run"]}, indent=2))
    print(json.dumps({"baseline": baseline_report["release_report"], "candidate": candidate_report["release_report"]}, indent=2))


if __name__ == "__main__":
    main()
