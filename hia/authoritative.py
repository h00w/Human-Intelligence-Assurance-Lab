from __future__ import annotations

PHASE_1_8_AUTHORITATIVE = {
    "decision": "SHIP",
    "workflow_run_id": 34763385977,
    "artifact_id": 10319148905,
    "source_commit": "50e3173ef0b8796466c9fe0784057a7906228218",
    "publication_commit": "67d4a12ddc714e08fdc538f9031fa7cb98f31ca4",
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "primary": "nscale",
    "fallback": "novita",
    "derived_delays_ms": {
        "critical": 1223.45,
        "high": 1323.25,
        "medium": 1504.93,
        "low": 2104.65,
    },
    "fallback_timeout_s": 6.276,
    "adaptive_redundant_token_rate": 0.1766,
    "fixed_redundant_token_rate": 0.2994,
    "adaptive_redundant_cost_usd": 0.00005621,
    "fixed_redundant_cost_usd": 0.00011488,
    "critical_fault_trials": (
        {"trial": 1, "decision": "SHIP", "mean_latency_ms": 2219.51, "p95_latency_ms": 2463.75},
        {"trial": 2, "decision": "SHIP", "mean_latency_ms": 2637.61, "p95_latency_ms": 5113.90},
        {"trial": 3, "decision": "SHIP", "mean_latency_ms": 2272.32, "p95_latency_ms": 2624.08},
    ),
    "scope": "tested benchmark/model/policy/provider routes/configuration/injected-fault model/observation window",
}
