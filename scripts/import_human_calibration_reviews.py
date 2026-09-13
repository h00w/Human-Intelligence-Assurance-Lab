from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from hia.review_execution import (
    ADJUDICATION_FIELDS,
    MERGED_FIELDS,
    apply_adjudications,
    csv_bytes,
    merge_independent_reviews,
    queue_fingerprint,
    validate_frozen_queue,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
DEFAULT_QUEUE = ARTIFACTS / "human_review_queue.csv"
DEFAULT_OUT = ARTIFACTS / "human_calibration_import"


def read_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8", newline="")))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate, merge, and adjudicate independent HIA-Lab human reviews.")
    parser.add_argument("reviewer_a", type=Path)
    parser.add_argument("reviewer_b", type=Path)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    frozen = read_csv(args.queue)
    validate_frozen_queue(frozen)
    result = merge_independent_reviews(frozen, [read_csv(args.reviewer_a), read_csv(args.reviewer_b)])
    args.out.mkdir(parents=True, exist_ok=True)

    merged_rows = list(result.merged_rows)
    adjudication_path = args.out / "adjudication_queue.csv"
    adjudication_path.write_bytes(csv_bytes(result.adjudication_rows, ADJUDICATION_FIELDS))

    status = "READY_FOR_SCORING"
    if result.disagreement_count:
        if args.adjudication is None:
            status = "ADJUDICATION_REQUIRED"
        else:
            merged_rows = apply_adjudications(merged_rows, read_csv(args.adjudication))

    merged_path = args.out / "merged_human_labels.csv"
    merged_path.write_bytes(csv_bytes(merged_rows, MERGED_FIELDS))
    manifest = {
        "schema_version": "1.0",
        "frozen_queue_sha256": queue_fingerprint(frozen),
        "reviewers": list(result.reviewer_ids),
        "sample_count": result.sample_count,
        "disagreement_count": result.disagreement_count,
        "status": status,
        "merged_labels": str(merged_path),
        "adjudication_queue": str(adjudication_path),
        "note": "Original reviewer labels are preserved. Disagreements require explicit adjudication before release-critical scoring.",
    }
    (args.out / "import_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

    if status == "ADJUDICATION_REQUIRED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
