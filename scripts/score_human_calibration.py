from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files

from hia.calibration import calibration_report

ROOT = Path(__file__).resolve().parents[1]
INPUT = Path(os.getenv("HIA_HUMAN_REVIEW_CSV", ROOT / "artifacts" / "human_review_queue.csv"))
OUT = ROOT / "artifacts" / "calibration_report.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _parse_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "pass"}:
        return True
    if normalized in {"false", "0", "no", "fail"}:
        return False
    return None


def main() -> None:
    rows = list(csv.DictReader(INPUT.open(encoding="utf-8", newline="")))
    labeled = []
    for row in rows:
        human = _parse_bool(row.get("human_pass", ""))
        judge = _parse_bool(row.get("judge_pass", ""))
        if human is None or judge is None:
            continue
        reviewer = row.get("reviewer", "").strip()
        if not reviewer:
            raise ValueError(f"reviewer provenance missing for scenario {row.get('scenario_id', 'unknown')}")
        labeled.append((human, judge, row.get("risk_level") == "critical"))

    if not labeled:
        raise ValueError("no independently labeled rows found")

    report = calibration_report(
        human_labels=[row[0] for row in labeled],
        judge_labels=[row[1] for row in labeled],
        critical_flags=[row[2] for row in labeled],
    )
    payload = {
        "schema_version": "1.3",
        "source": str(INPUT),
        "reviewed_rows": len(labeled),
        "report": asdict(report),
        "semantic_release_critical": bool(report.calibrated),
        "note": (
            "Calibration metrics are computed only from rows with explicit human labels and reviewer provenance. "
            "This report does not auto-generate human judgments."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

    token = os.getenv("HF_TOKEN")
    if token:
        api = HfApi(token=token)
        api.upload_file(
            path_or_fileobj=str(OUT),
            path_in_repo="runs/calibration_report.json",
            repo_id=DATASET_REPO,
            repo_type="dataset",
        )
        batch_bucket_files(
            BUCKET,
            add=[(str(OUT), "runs/calibration_report.json")],
            token=token,
        )


if __name__ == "__main__":
    main()
