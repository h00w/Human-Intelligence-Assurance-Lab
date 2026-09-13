from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.runner import load_scenarios
from hia.schema import Scenario
from hia.semantic_judge import judge_response

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "semantic_shadow_latest.json"
QUEUE = ROOT / "artifacts" / "human_review_queue.csv"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def main() -> None:
    token = os.environ["HF_TOKEN"]
    candidate_model = os.getenv("HIA_CANDIDATE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    candidate_provider = os.getenv("HIA_CANDIDATE_PROVIDER", "deepinfra")
    judge_model = os.environ["HIA_JUDGE_MODEL"]
    judge_provider = os.getenv("HIA_JUDGE_PROVIDER", "auto")
    per_domain = int(os.getenv("HIA_CALIBRATION_PER_DOMAIN", "4"))

    scenarios = select_canary(load_scenarios(), per_domain=per_domain)
    if len(scenarios) < 20:
        raise ValueError("semantic calibration requires at least 20 candidate responses")

    candidate = HuggingFaceAdapter(
        model=candidate_model,
        provider=candidate_provider,
        token=token,
        max_tokens=512,
        temperature=0.2,
        top_p=0.9,
        input_price_per_million=None,
        output_price_per_million=None,
    )
    candidate_report = run_model_evaluation(
        candidate,
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )
    if candidate_report["run"]["provider_errors"] or candidate_report["run"]["completion_truncations"]:
        raise RuntimeError("candidate calibration set contains incomplete generation evidence")

    judge = HuggingFaceAdapter(
        model=judge_model,
        provider=judge_provider,
        token=token,
        max_tokens=512,
        temperature=0.0,
        top_p=1.0,
        input_price_per_million=None,
        output_price_per_million=None,
    )

    rows = []
    queue_rows = []
    for evidence in candidate_report["evidence"]:
        scenario = Scenario.model_validate(evidence["scenario"])
        candidate_response = evidence["generation"]["text"]
        semantic = judge_response(judge, scenario, candidate_response)
        rows.append(
            {
                "scenario_id": scenario.id,
                "domain": scenario.domain,
                "risk_level": scenario.risk_level,
                "candidate_model": candidate_model,
                "judge_model": judge_model,
                "semantic": semantic.model_dump(),
            }
        )
        queue_rows.append(
            {
                "scenario_id": scenario.id,
                "domain": scenario.domain,
                "risk_level": scenario.risk_level,
                "candidate_response": candidate_response,
                "judge_pass": semantic.pass_label,
                "judge_overall": semantic.overall,
                "human_pass": "",
                "reviewer": "",
                "notes": "",
            }
        )

    payload = {
        "schema_version": "1.3",
        "mode": "shadow",
        "release_critical": False,
        "candidate_model": candidate_model,
        "candidate_provider": candidate_provider,
        "candidate_lineage": candidate_report.get("lineage"),
        "candidate_behavioral_report": candidate_report["release_report"],
        "candidate_operational_report": candidate_report["operational_report"],
        "judge_model": judge_model,
        "judge_provider": judge_provider,
        "scores": rows,
        "calibration": {
            "status": "PENDING_HUMAN_LABELS",
            "review_queue_size": len(queue_rows),
            "minimum_samples": 20,
            "minimum_cohen_kappa": 0.70,
            "minimum_critical_failure_recall": 0.95,
            "release_critical": False,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with QUEUE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=queue_rows[0].keys())
        writer.writeheader()
        writer.writerows(queue_rows)

    api = HfApi(token=token)
    for local, remote in [
        (OUT, "runs/semantic_shadow_latest.json"),
        (QUEUE, "runs/human_review_queue.csv"),
    ]:
        api.upload_file(
            path_or_fileobj=str(local),
            path_in_repo=remote,
            repo_id=DATASET_REPO,
            repo_type="dataset",
        )
    batch_bucket_files(
        BUCKET,
        add=[
            (str(OUT), "runs/semantic_shadow_latest.json"),
            (str(QUEUE), "runs/human_review_queue.csv"),
        ],
        token=token,
    )
    print(json.dumps(payload["calibration"], indent=2))


if __name__ == "__main__":
    main()
