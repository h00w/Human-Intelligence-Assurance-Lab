from __future__ import annotations

import argparse
import csv
from pathlib import Path

from hia.review_execution import (
    REVIEWER_FIELDS,
    csv_bytes,
    make_reviewer_sheet,
    validate_frozen_queue,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "artifacts" / "human_review_queue.csv"
DEFAULT_OUT = ROOT / "artifacts" / "human_review"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create blinded independent reviewer sheets from the frozen semantic review queue."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--reviewers",
        nargs="+",
        required=True,
        help="Opaque reviewer IDs, e.g. reviewer_A reviewer_B",
    )
    args = parser.parse_args()

    rows = list(csv.DictReader(args.input.open(encoding="utf-8", newline="")))
    validate_frozen_queue(rows)
    if len(set(args.reviewers)) != len(args.reviewers):
        raise ValueError("reviewer IDs must be unique")
    args.out.mkdir(parents=True, exist_ok=True)

    for reviewer_id in args.reviewers:
        target = args.out / f"review_{reviewer_id}.csv"
        target.write_bytes(csv_bytes(make_reviewer_sheet(rows, reviewer_id), REVIEWER_FIELDS))
        print(target)


if __name__ == "__main__":
    main()
