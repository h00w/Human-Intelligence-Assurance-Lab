from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "artifacts" / "human_review_queue.csv"
DEFAULT_OUT = ROOT / "artifacts" / "human_review"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create independent reviewer sheets from the frozen semantic review queue.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--reviewers", nargs="+", required=True, help="Opaque reviewer IDs, e.g. r1 r2")
    args = parser.parse_args()

    rows = list(csv.DictReader(args.input.open(encoding="utf-8", newline="")))
    if not rows:
        raise SystemExit("review queue is empty")
    args.out.mkdir(parents=True, exist_ok=True)

    fields = [
        "sample_id",
        "scenario_id",
        "domain",
        "risk_level",
        "candidate_response",
        "judge_pass",
        "judge_overall",
        "reviewer_id",
        "human_pass",
        "adjudicated_pass",
        "notes",
    ]
    for reviewer_id in args.reviewers:
        target = args.out / f"review_{reviewer_id}.csv"
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "sample_id": row["scenario_id"],
                        "scenario_id": row["scenario_id"],
                        "domain": row["domain"],
                        "risk_level": row["risk_level"],
                        "candidate_response": row["candidate_response"],
                        "judge_pass": row["judge_pass"],
                        "judge_overall": row["judge_overall"],
                        "reviewer_id": reviewer_id,
                        "human_pass": "",
                        "adjudicated_pass": "",
                        "notes": "",
                    }
                )
        print(target)


if __name__ == "__main__":
    main()
