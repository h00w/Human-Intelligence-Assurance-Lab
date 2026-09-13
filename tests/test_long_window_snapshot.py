from datetime import datetime, timezone

from scripts.run_long_window_qualification import snapshot_from_payload


def test_snapshot_includes_fault_recovery_failure():
    payload = {
        "executive_decision": {"decision": "HOLD"},
        "comparison": {
            "adaptive": {
                "report": {
                    "run": {
                        "mean_latency_ms": 1300,
                        "p95_latency_ms": 2600,
                        "provider_errors": 0,
                        "completion_truncations": 0,
                    },
                    "release_report": {"blocker_failures": 0},
                    "production_decision": {"decision": "SHIP"},
                },
                "economics": {"redundant_cost_rate": 0.12},
            }
        },
        "critical_fault_recovery": {
            "trials": [
                {
                    "trial": 1,
                    "report": {
                        "run": {"provider_errors": 1, "completion_truncations": 0},
                        "release_report": {"blocker_failures": 0},
                        "production_decision": {"decision": "HOLD"},
                    },
                }
            ]
        },
    }
    snapshot = snapshot_from_payload(payload, datetime(2026, 9, 13, tzinfo=timezone.utc))
    assert snapshot.production_decision == "HOLD"
    assert snapshot.provider_errors == 1
    assert snapshot.mean_latency_ms == 1300
