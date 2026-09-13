from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from hia.adapters import HuggingFaceAdapter
from hia.semantic_judge import judge_response
from hia.schema import Scenario

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "semantic_shadow_latest.json"
QUEUE = ROOT / "artifacts" / "human_review_queue.csv"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"


def main() -> None:
    judge_model = os.environ["HIA_JUDGE_MODEL"]
    judge_provider = os.getenv("HIA_JUDGE_PROVIDER", "auto")
    token = os.environ["HF_TOKEN"]

    latest_path = hf_hub_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        filename="runs/live_eval_latest.json",
        token=token,
    )
    latest = json.loads(Path(latest_path).read_text(encoding="utf-8"))
    judge = HuggingFaceAdapter(
        model=judge_model,
        provider=judge_provider,
        token=token,
        max_tokens=512,
        temperature=0.0,
        input_price_per_million=None,
        output_price_per_million=None,
    )

    rows = []
    queue_rows = []
    for evidence in latest["evidence"]:
        scenario = Scenario.model_validate(evidence["scenario"])
        candidate_response = evidence["generation"]["text"]
        semantic = judge_response(judge, scenario, candidate_response)
        rows.append(
            {
                "scenario_id": scenario.id,
                "domain": scenario.domain,
                "risk_level": scenario.risk_level,
                "candidate_model": latest["run"]["model"],
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
        "schema_version": "1.2",
        "mode": "shadow",
        "release_critical": False,
        "candidate_lineage": latest.get("lineage"),
        "judge_model": judge_model,
        "judge_provider": judge_provider,
        "scores": rows,
        "calibration": {
            "status": "PENDING_HUMAN_LABELS",
            "minimum_samples": 20,
            "minimum_cohen_kappa": 0.70,
            "minimum_critical_failure_recall": 0.95,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with QUEUE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=queue_rows[0].keys())
        writer.writeheader()
        writer.writerows(queue_rows)

    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/semantic_shadow_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    api.upload_file(
        path_or_fileobj=str(QUEUE),
        path_in_repo="runs/human_review_queue.csv",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    print(json.dumps(payload["calibration"], indent=2))


if __name__ == "__main__":
    main()
