from __future__ import annotations

import csv
import hashlib
import io
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

REVIEWER_FIELDS = (
    "sample_id",
    "scenario_id",
    "domain",
    "risk_level",
    "candidate_response",
    "reviewer_id",
    "human_pass",
    "notes",
)

ADJUDICATION_FIELDS = (
    "sample_id",
    "scenario_id",
    "reviewer_a_pass",
    "reviewer_b_pass",
    "adjudicator_id",
    "adjudicated_pass",
    "adjudication_notes",
)

MERGED_FIELDS = (
    "sample_id",
    "scenario_id",
    "domain",
    "risk_level",
    "judge_pass",
    "reviewer_id",
    "human_pass",
    "adjudicated_pass",
    "notes",
)


@dataclass(frozen=True, slots=True)
class ReviewImportResult:
    merged_rows: tuple[dict[str, str], ...]
    adjudication_rows: tuple[dict[str, str], ...]
    reviewer_ids: tuple[str, ...]
    sample_count: int
    disagreement_count: int


def parse_bool(value: object) -> bool | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes", "pass"}:
        return True
    if normalized in {"false", "0", "no", "fail"}:
        return False
    return None


def bool_text(value: bool | None) -> str:
    if value is None:
        return ""
    return "true" if value else "false"


def csv_bytes(rows: Iterable[Mapping[str, object]], fields: Iterable[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    return stream.getvalue().encode("utf-8")


def queue_fingerprint(rows: Iterable[Mapping[str, object]]) -> str:
    """Fingerprint only immutable candidate evidence visible to human reviewers.

    Judge output is deliberately excluded so the human batch can be frozen before
    any semantic-judge call and the judge can be evaluated after independent review.
    """
    canonical = []
    for row in rows:
        canonical.append(
            "\x1f".join(
                str(row.get(key, ""))
                for key in (
                    "scenario_id",
                    "domain",
                    "risk_level",
                    "candidate_response",
                )
            )
        )
    payload = "\x1e".join(sorted(canonical)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_frozen_queue(rows: list[dict[str, str]], *, minimum_samples: int = 20) -> None:
    if len(rows) < minimum_samples:
        raise ValueError(f"frozen review queue requires at least {minimum_samples} rows")
    required = {
        "scenario_id",
        "domain",
        "risk_level",
        "candidate_response",
    }
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"frozen queue missing required columns: {sorted(missing)}")
    ids = [row["scenario_id"].strip() for row in rows]
    if any(not item for item in ids):
        raise ValueError("frozen queue contains blank scenario_id")
    if len(ids) != len(set(ids)):
        raise ValueError("frozen queue contains duplicate scenario_id")
    for row in rows:
        if (
            "judge_pass" in row
            and row.get("judge_pass", "").strip()
            and parse_bool(row.get("judge_pass")) is None
        ):
            raise ValueError(f"invalid frozen judge_pass for {row['scenario_id']}")
        if not row.get("candidate_response", "").strip():
            raise ValueError(f"candidate response missing for {row['scenario_id']}")


def make_reviewer_sheet(rows: list[dict[str, str]], reviewer_id: str) -> list[dict[str, str]]:
    validate_frozen_queue(rows)
    reviewer_id = reviewer_id.strip()
    if not reviewer_id:
        raise ValueError("reviewer_id cannot be blank")
    return [
        {
            "sample_id": row["scenario_id"],
            "scenario_id": row["scenario_id"],
            "domain": row["domain"],
            "risk_level": row["risk_level"],
            "candidate_response": row["candidate_response"],
            "reviewer_id": reviewer_id,
            "human_pass": "",
            "notes": "",
        }
        for row in rows
    ]


def _validate_reviewer_sheet(
    frozen_by_id: dict[str, dict[str, str]],
    rows: list[dict[str, str]],
    expected_reviewer_id: str | None = None,
) -> str:
    if not rows:
        raise ValueError("reviewer sheet is empty")
    reviewer_ids = {row.get("reviewer_id", "").strip() for row in rows}
    if "" in reviewer_ids or len(reviewer_ids) != 1:
        raise ValueError("each reviewer sheet must contain exactly one non-empty reviewer_id")
    reviewer_id = next(iter(reviewer_ids))
    if expected_reviewer_id and reviewer_id != expected_reviewer_id:
        raise ValueError(f"expected reviewer_id {expected_reviewer_id}, received {reviewer_id}")

    seen: set[str] = set()
    for row in rows:
        sample_id = (row.get("sample_id") or row.get("scenario_id") or "").strip()
        if sample_id not in frozen_by_id:
            raise ValueError(f"unknown sample_id in reviewer sheet: {sample_id}")
        if sample_id in seen:
            raise ValueError(f"duplicate sample_id in reviewer sheet: {sample_id}")
        seen.add(sample_id)
        frozen = frozen_by_id[sample_id]
        for key in ("scenario_id", "domain", "risk_level", "candidate_response"):
            if row.get(key, "") != frozen.get(key, ""):
                raise ValueError(f"frozen field {key} changed for {sample_id}")
        if parse_bool(row.get("human_pass")) is None:
            raise ValueError(f"human_pass missing or invalid for {sample_id}")

    expected = set(frozen_by_id)
    if seen != expected:
        missing = sorted(expected - seen)
        raise ValueError(f"reviewer sheet does not cover the frozen batch; missing={missing}")
    return reviewer_id


def merge_independent_reviews(
    frozen_rows: list[dict[str, str]],
    reviewer_sheets: Iterable[list[dict[str, str]]],
) -> ReviewImportResult:
    validate_frozen_queue(frozen_rows)
    frozen_by_id = {row["scenario_id"]: row for row in frozen_rows}
    sheets = list(reviewer_sheets)
    if len(sheets) < 2:
        raise ValueError("at least two independent reviewer sheets are required")

    reviewer_ids: list[str] = []
    by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for sheet in sheets:
        reviewer_id = _validate_reviewer_sheet(frozen_by_id, sheet)
        if reviewer_id in reviewer_ids:
            raise ValueError(f"reviewer_id reused across sheets: {reviewer_id}")
        reviewer_ids.append(reviewer_id)
        for row in sheet:
            sample_id = (row.get("sample_id") or row.get("scenario_id") or "").strip()
            by_sample[sample_id].append(row)

    merged: list[dict[str, str]] = []
    adjudication: list[dict[str, str]] = []
    for sample_id in sorted(frozen_by_id):
        frozen = frozen_by_id[sample_id]
        sample_rows = sorted(by_sample[sample_id], key=lambda row: row["reviewer_id"])
        values = [parse_bool(row["human_pass"]) for row in sample_rows]
        if len(set(values)) > 1:
            adjudication.append(
                {
                    "sample_id": sample_id,
                    "scenario_id": sample_id,
                    "reviewer_a_pass": bool_text(values[0]),
                    "reviewer_b_pass": bool_text(values[1]),
                    "adjudicator_id": "",
                    "adjudicated_pass": "",
                    "adjudication_notes": "",
                }
            )
        judge_pass = parse_bool(frozen.get("judge_pass", ""))
        for row in sample_rows:
            merged.append(
                {
                    "sample_id": sample_id,
                    "scenario_id": sample_id,
                    "domain": frozen["domain"],
                    "risk_level": frozen["risk_level"],
                    "judge_pass": bool_text(judge_pass),
                    "reviewer_id": row["reviewer_id"],
                    "human_pass": bool_text(parse_bool(row["human_pass"])),
                    "adjudicated_pass": "",
                    "notes": row.get("notes", ""),
                }
            )

    return ReviewImportResult(
        merged_rows=tuple(merged),
        adjudication_rows=tuple(adjudication),
        reviewer_ids=tuple(sorted(reviewer_ids)),
        sample_count=len(frozen_by_id),
        disagreement_count=len(adjudication),
    )


def apply_adjudications(
    merged_rows: Iterable[Mapping[str, str]],
    adjudication_rows: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in merged_rows]
    adjudications: dict[str, bool] = {}
    for row in adjudication_rows:
        sample_id = (row.get("sample_id") or row.get("scenario_id") or "").strip()
        if not sample_id:
            raise ValueError("adjudication row missing sample_id")
        adjudicator = str(row.get("adjudicator_id", "")).strip()
        value = parse_bool(row.get("adjudicated_pass"))
        if not adjudicator or value is None:
            raise ValueError(f"adjudication incomplete for {sample_id}")
        if sample_id in adjudications:
            raise ValueError(f"duplicate adjudication for {sample_id}")
        adjudications[sample_id] = value

    grouped: dict[str, set[bool]] = defaultdict(set)
    for row in rows:
        sample_id = row["sample_id"]
        value = parse_bool(row.get("human_pass"))
        if value is None:
            raise ValueError(f"invalid human_pass for {sample_id}")
        grouped[sample_id].add(value)
    disagreements = {sample_id for sample_id, votes in grouped.items() if len(votes) > 1}
    if set(adjudications) != disagreements:
        missing = sorted(disagreements - set(adjudications))
        extra = sorted(set(adjudications) - disagreements)
        raise ValueError(f"adjudication set mismatch; missing={missing}, extra={extra}")

    for row in rows:
        if row["sample_id"] in adjudications:
            row["adjudicated_pass"] = bool_text(adjudications[row["sample_id"]])
    return rows
