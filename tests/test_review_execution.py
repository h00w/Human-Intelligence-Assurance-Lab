from hia.review_execution import apply_adjudications, make_reviewer_sheet, merge_independent_reviews, queue_fingerprint


def frozen_rows():
    rows = []
    for idx in range(20):
        rows.append(
            {
                "scenario_id": f"hia-{idx:03d}",
                "domain": "vulnerability" if idx < 5 else "everyday_affect",
                "risk_level": "critical" if idx < 5 else "low",
                "candidate_response": f"response {idx}",
                "judge_pass": "false" if idx == 0 else "true",
                "judge_overall": "0.8",
            }
        )
    return rows


def label(sheet, default="true"):
    return [{**row, "human_pass": default} for row in sheet]


def test_reviewer_sheet_is_blinded_to_judge_output():
    sheet = make_reviewer_sheet(frozen_rows(), "reviewer_A")
    assert len(sheet) == 20
    assert all("judge_pass" not in row for row in sheet)
    assert all("judge_overall" not in row for row in sheet)
    assert {row["reviewer_id"] for row in sheet} == {"reviewer_A"}


def test_queue_fingerprint_changes_when_frozen_response_changes():
    rows = frozen_rows()
    before = queue_fingerprint(rows)
    rows[0] = {**rows[0], "candidate_response": "mutated"}
    assert queue_fingerprint(rows) != before


def test_import_rejects_modified_frozen_field():
    frozen = frozen_rows()
    a = label(make_reviewer_sheet(frozen, "reviewer_A"))
    b = label(make_reviewer_sheet(frozen, "reviewer_B"))
    b[3] = {**b[3], "candidate_response": "changed response"}
    try:
        merge_independent_reviews(frozen, [a, b])
    except ValueError as exc:
        assert "frozen field candidate_response changed" in str(exc)
    else:
        raise AssertionError("modified frozen field must be rejected")


def test_disagreement_requires_explicit_adjudication():
    frozen = frozen_rows()
    a = label(make_reviewer_sheet(frozen, "reviewer_A"))
    b = label(make_reviewer_sheet(frozen, "reviewer_B"))
    b[0] = {**b[0], "human_pass": "false"}
    result = merge_independent_reviews(frozen, [a, b])
    assert result.disagreement_count == 1
    assert result.adjudication_rows[0]["sample_id"] == "hia-000"

    adjudicated = apply_adjudications(
        result.merged_rows,
        [
            {
                "sample_id": "hia-000",
                "adjudicator_id": "adjudicator_1",
                "adjudicated_pass": "false",
            }
        ],
    )
    resolved = [row for row in adjudicated if row["sample_id"] == "hia-000"]
    assert {row["adjudicated_pass"] for row in resolved} == {"false"}


def test_duplicate_reviewer_identity_is_rejected():
    frozen = frozen_rows()
    a = label(make_reviewer_sheet(frozen, "reviewer_A"))
    b = label(make_reviewer_sheet(frozen, "reviewer_A"))
    try:
        merge_independent_reviews(frozen, [a, b])
    except ValueError as exc:
        assert "reviewer_id reused" in str(exc)
    else:
        raise AssertionError("same reviewer cannot satisfy independent review requirement")
