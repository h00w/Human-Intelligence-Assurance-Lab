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
