from dataclasses import replace

import pytest

from hia.comparison import CandidateSummary, compare_candidates


def summary(name="candidate"):
    return CandidateSummary(name, "SHIP", 1.0, 0.9, 10.0, 0.01)


@pytest.mark.parametrize("field,invalid", [
    ("name", " "), ("name", None), ("decision", "UNKNOWN"),
    ("pass_rate", float("nan")), ("pass_rate", 1.1), ("pass_rate", True),
    ("semantic_score", float("inf")), ("semantic_score", -0.1),
    ("mean_latency_ms", float("nan")), ("mean_latency_ms", -1),
    ("estimated_cost_usd", float("inf")), ("estimated_cost_usd", -1),
    ("blocker_failures", -1), ("blocker_failures", True), ("blocker_failures", 0.5),
])
@pytest.mark.parametrize("role", ["baseline", "candidate"])
def test_invalid_summary_cannot_win_comparison(field, invalid, role):
    valid = summary("valid")
    invalid_summary = replace(summary("invalid"), **{field: invalid})
    rows = (invalid_summary, valid) if role == "baseline" else (valid, invalid_summary)
    with pytest.raises(ValueError, match="summary"):
        compare_candidates(*rows)


def test_unmeasured_optional_metrics_remain_valid():
    a = replace(summary("a"), semantic_score=None, mean_latency_ms=None, estimated_cost_usd=None)
    b = replace(a, name="b")
    assert compare_candidates(a, b).winner == "TIE"
