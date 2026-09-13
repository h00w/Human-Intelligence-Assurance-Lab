from hia.adaptive import AdaptiveHedgePolicy, cohort_metrics, routing_economics


def test_adaptive_policy_hedges_critical_no_later_than_ordinary():
    policy = AdaptiveHedgePolicy.from_latencies([600, 800, 1000, 1200, 1500, 1800, 2200, 2600])
    assert policy.delay_for("critical") <= policy.delay_for("high")
    assert policy.delay_for("high") <= policy.delay_for("medium")
    assert policy.delay_for("medium") <= policy.delay_for("low")
    assert policy.delay_for("critical") >= 500
    assert policy.delay_for("low") <= 2500


def test_routing_economics_counts_redundant_work():
    report = {
        "evidence": [
            {
                "error": None,
                "generation": {
                    "total_tokens": 100,
                    "estimated_cost_usd": 0.001,
                    "metadata": {
                        "hedge_used": True,
                        "winning_role": "primary",
                        "observed_total_tokens": 180,
                        "observed_estimated_cost_usd": 0.0016,
                    },
                },
            }
        ]
    }
    economics = routing_economics(report)
    assert economics["redundant_tokens"] == 80
    assert economics["redundant_cost_usd"] == 0.0006
    assert economics["hedge_rate"] == 1.0


def test_cohort_metrics_keep_risk_groups_separate():
    report = {
        "evidence": [
            {
                "error": None,
                "scenario": {"risk_level": "critical"},
                "evaluation": {"passed": True},
                "generation": {
                    "latency_ms": 1000,
                    "total_tokens": 100,
                    "estimated_cost_usd": 0.001,
                    "metadata": {
                        "hedge_used": True,
                        "winning_role": "fallback",
                        "observed_total_tokens": 200,
                        "observed_estimated_cost_usd": 0.002,
                    },
                },
            },
            {
                "error": None,
                "scenario": {"risk_level": "low"},
                "evaluation": {"passed": True},
                "generation": {
                    "latency_ms": 800,
                    "total_tokens": 90,
                    "estimated_cost_usd": 0.0008,
                    "metadata": {
                        "hedge_used": False,
                        "winning_role": "primary",
                        "observed_total_tokens": 90,
                        "observed_estimated_cost_usd": 0.0008,
                    },
                },
            },
        ]
    }
    cohorts = cohort_metrics(report)
    assert cohorts["critical"]["hedge_rate"] == 1.0
    assert cohorts["low"]["hedge_rate"] == 0.0
