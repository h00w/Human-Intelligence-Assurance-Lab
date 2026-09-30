from hia.human_calibration import HumanLabel, evaluate_human_calibration


def _rows(count: int = 20):
    rows = []
    for idx in range(count):
        human_pass = idx % 5 != 0
        critical = idx < 5
        for reviewer in ("r1", "r2"):
            rows.append(
                HumanLabel(
                    sample_id=f"s{idx:02d}",
                    reviewer_id=reviewer,
                    human_pass=human_pass,
                    judge_pass=human_pass,
                    critical=critical,
                )
            )
    return rows


def test_independent_calibration_can_pass():
    result = evaluate_human_calibration(_rows())
    assert result.ready_for_release is True
    assert result.sample_count == 20
    assert result.reviewer_count == 2
    assert result.inter_reviewer_kappa == 1.0
    assert result.judge_calibration is not None
    assert result.judge_calibration.calibrated is True


def test_no_critical_failure_cannot_claim_perfect_recall():
    rows = [
        HumanLabel(sample_id=f"s{i:02d}", reviewer_id=reviewer,
                   human_pass=i % 2 == 0, judge_pass=i % 2 == 0, critical=False)
        for i in range(20) for reviewer in ("r1", "r2")
    ]
    result = evaluate_human_calibration(rows)
    assert result.ready_for_release is False
    assert result.judge_calibration is not None
    assert result.judge_calibration.critical_failure_count == 0
    assert result.judge_calibration.critical_recall == 0.0


def test_single_reviewer_cannot_unlock_release():
    rows = [row for row in _rows() if row.reviewer_id == "r1"]
    result = evaluate_human_calibration(rows)
    assert result.ready_for_release is False
    assert result.sample_count == 0
    assert result.unresolved_count == 20


def test_disagreement_requires_adjudication():
    rows = _rows()
    rows[1] = HumanLabel(
        sample_id=rows[1].sample_id,
        reviewer_id=rows[1].reviewer_id,
        human_pass=not rows[1].human_pass,
        judge_pass=rows[1].judge_pass,
        critical=rows[1].critical,
    )
    result = evaluate_human_calibration(rows)
    assert result.ready_for_release is False
    assert result.unresolved_count >= 1


def test_duplicate_reviewer_cannot_be_counted_twice():
    rows = _rows()
    rows.append(rows[0])
    result = evaluate_human_calibration(rows)
    assert result.ready_for_release is False
    assert result.unresolved_count == 1


def test_reviewer_case_variants_do_not_count_as_independent():
    rows = _rows()
    rows[1] = HumanLabel(
        sample_id=rows[0].sample_id,
        reviewer_id="R1",
        human_pass=rows[0].human_pass,
        judge_pass=rows[0].judge_pass,
        critical=rows[0].critical,
    )
    result = evaluate_human_calibration(rows)
    assert result.ready_for_release is False
    assert result.unresolved_count == 1


def test_conflicting_adjudications_cannot_unlock_release():
    rows = _rows()
    rows[1] = HumanLabel(
        sample_id=rows[1].sample_id,
        reviewer_id=rows[1].reviewer_id,
        human_pass=not rows[1].human_pass,
        judge_pass=rows[1].judge_pass,
        critical=rows[1].critical,
        adjudicated_pass=False,
    )
    rows[0] = HumanLabel(
        sample_id=rows[0].sample_id,
        reviewer_id=rows[0].reviewer_id,
        human_pass=rows[0].human_pass,
        judge_pass=rows[0].judge_pass,
        critical=rows[0].critical,
        adjudicated_pass=True,
    )
    result = evaluate_human_calibration(rows)
    assert result.ready_for_release is False
    assert result.unresolved_count == 1
