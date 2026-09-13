from __future__ import annotations

import json
import os
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.runner import load_scenarios

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "live_eval_latest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def main() -> None:
    model = os.getenv("HIA_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    per_domain = int(os.getenv("HIA_CANARY_PER_DOMAIN", "2"))
    scenarios = select_canary(load_scenarios(), per_domain=per_domain)
    report = run_model_evaluation(HuggingFaceAdapter(model=model), scenarios)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/live_eval_latest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(
        BUCKET,
        add=[(str(OUT), "runs/live_eval_latest.json")],
        token=token,
    )
    print(json.dumps(report["run"], indent=2))
    print(json.dumps(report["release_report"], indent=2))


if __name__ == "__main__":
    main()
