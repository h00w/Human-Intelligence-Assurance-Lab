from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.adapters import HuggingFaceAdapter
from hia.review_execution import (
    MERGED_FIELDS,
    bool_text,
    csv_bytes,
    queue_fingerprint,
    validate_frozen_queue,
)
from hia.runner import load_scenarios
from hia.semantic_judge import judge_response

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
QUEUE = Path(os.getenv("HIA_FROZEN_REVIEW_QUEUE", ARTIFACTS / "human_review_queue.csv"))
HUMAN_LABELS = Path(
    os.getenv(
        "HIA_HUMAN_REVIEW_CSV",
        ARTIFACTS / "human_calibration_import" / "merged_human_labels.csv",
    )
)
OUT_DIR = ARTIFACTS / "human_calibration_judge"
SCORING_INPUT = OUT_DIR / "calibration_scoring_input.csv"
JUDGE_REPORT = OUT_DIR / "post_review_semantic_judge.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    token = os.environ["HF_TOKEN"]
    judge_model = os.environ["HIA_JUDGE_MODEL"]
    judge_provider = os.getenv("HIA_JUDGE_PROVIDER", "auto")

    queue = read_csv(QUEUE)
    validate_frozen_queue(queue)
    human_rows = read_csv(HUMAN_LABELS)
    if not human_rows:
        raise ValueError("validated human-review input is empty")

    queue_by_id = {row["scenario_id"]: row for row in queue}
    reviewed_ids = {row.get("sample_id", "").strip() for row in human_rows}
    if reviewed_ids != set(queue_by_id):
        raise ValueError("human-review sample set does not exactly match frozen review queue")
    for row in human_rows:
        if not row.get("human_pass", "").strip():
            raise ValueError(f"human label missing for {row.get('sample_id', 'unknown')}")

    scenarios = {scenario.id: scenario for scenario in load_scenarios()}
    missing_scenarios = sorted(set(queue_by_id) - set(scenarios))
    if missing_scenarios:
        raise ValueError(f"frozen samples not found in benchmark corpus: {missing_scenarios}")

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

    judge_rows: list[dict[str, object]] = []
    judge_by_id: dict[str, bool] = {}
    for sample_id in sorted(queue_by_id):
        frozen = queue_by_id[sample_id]
        semantic = judge_response(judge, scenarios[sample_id], frozen["candidate_response"])
        judge_by_id[sample_id] = semantic.pass_label
        judge_rows.append(
            {
                "sample_id": sample_id,
                "judge_pass": semantic.pass_label,
                "judge_overall": semantic.overall,
                "scores": semantic.model_dump(),
            }
        )

    scoring_rows: list[dict[str, str]] = []
    for row in human_rows:
        sample_id = row["sample_id"]
        scoring_rows.append({**row, "judge_pass": bool_text(judge_by_id[sample_id])})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCORING_INPUT.write_bytes(csv_bytes(scoring_rows, MERGED_FIELDS))
    report = {
        "schema_version": "1.0",
        "mode": "post_review_shadow",
        "release_critical": False,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "frozen_queue_sha256": queue_fingerprint(queue),
        "sample_count": len(queue),
        "judge_model": judge_model,
        "judge_provider": judge_provider,
        "scores": judge_rows,
        "scoring_input": str(SCORING_INPUT),
        "note": (
            "Judge labels were generated only after independent human review was complete. "
            "This prevents judge-output anchoring. Release-critical status is determined separately by calibration."
        ),
    }
    JUDGE_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key != "scores"}, indent=2))

    if os.getenv("HIA_PUBLISH_POST_REVIEW_JUDGE") == "1":
        api = HfApi(token=token)
        for local, remote in (
            (JUDGE_REPORT, "runs/post_review_semantic_judge.json"),
            (SCORING_INPUT, "runs/calibration_scoring_input.csv"),
        ):
            api.upload_file(
                path_or_fileobj=str(local),
                path_in_repo=remote,
                repo_id=DATASET_REPO,
                repo_type="dataset",
            )
        batch_bucket_files(
            BUCKET,
            add=[
                (str(JUDGE_REPORT), "runs/post_review_semantic_judge.json"),
                (str(SCORING_INPUT), "runs/calibration_scoring_input.csv"),
            ],
            token=token,
        )


if __name__ == "__main__":
    main()
