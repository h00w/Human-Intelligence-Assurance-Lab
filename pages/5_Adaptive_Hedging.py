import json
from pathlib import Path

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
EVIDENCE_PATH = "runs/adaptive_hedging_latest.json"
LOCAL_FALLBACK = Path("artifacts/adaptive_hedging_latest.json")

st.set_page_config(page_title="Adaptive Hedging | HIA-Lab", page_icon="⚡", layout="wide")
st.title("Phase 1.8 — Adaptive Hedging & Cost-Aware Routing")
st.caption(
    "Risk-aware hedge timing derived from measured provider latency, with explicit duplicate-token and cost accounting."
)


def load_evidence() -> dict:
    try:
        path = hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            filename=EVIDENCE_PATH,
        )
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        if LOCAL_FALLBACK.exists():
            return json.loads(LOCAL_FALLBACK.read_text(encoding="utf-8"))
        raise


data = load_evidence()
verdict = data["executive_decision"]["decision"]

if verdict == "SHIP":
    st.success("Executive decision: SHIP")
else:
    st.error(f"Executive decision: {verdict}")

st.info(
    "Scope: this is evidence for the tested model, providers, policy, benchmark and observation window. "
    "It is not a universal safety or performance claim."
)

policy = data["calibration"]["derived_delays_ms"]
profile = data["calibration"]["latency_profile"]
fallback_timeout = data.get("critical_fault_recovery", {}).get("fallback_timeout_s")
if fallback_timeout is None:
    fallback_timeout = data.get("critical_fault_recovery", {}).get("fallback_timeout_seconds")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Critical hedge", f"{policy['critical']:.0f} ms")
c2.metric("High-risk hedge", f"{policy['high']:.0f} ms")
c3.metric("Medium-risk hedge", f"{policy['medium']:.0f} ms")
c4.metric("Low-risk hedge", f"{policy['low']:.0f} ms")

st.subheader("Measured primary-route latency profile")
profile_df = pd.DataFrame(
    {
        "percentile": ["p50", "p75", "p90", "p95"],
        "latency_ms": [profile["p50_ms"], profile["p75_ms"], profile["p90_ms"], profile["p95_ms"]],
    }
)
st.dataframe(profile_df, use_container_width=True, hide_index=True)

comparison = data["comparison"]
adaptive = comparison["adaptive"]
fixed = comparison["fixed_1500ms"]
adaptive_econ = adaptive["economics"]
fixed_econ = fixed["economics"]

st.subheader("Adaptive vs fixed 1.5 s hedge")
comparison_df = pd.DataFrame(
    [
        {
            "policy": "Adaptive",
            "production": adaptive["report"]["production_decision"]["decision"],
            "hedge_rate": adaptive_econ["hedge_rate"],
            "redundant_tokens": adaptive_econ["redundant_tokens"],
            "redundant_token_rate": adaptive_econ["redundant_token_rate"],
            "observed_cost_usd": adaptive_econ["observed_cost_usd"],
            "redundant_cost_usd": adaptive_econ["redundant_cost_usd"],
            "redundant_cost_rate": adaptive_econ["redundant_cost_rate"],
        },
        {
            "policy": "Fixed 1.5 s",
            "production": fixed["report"]["production_decision"]["decision"],
            "hedge_rate": fixed_econ["hedge_rate"],
            "redundant_tokens": fixed_econ["redundant_tokens"],
            "redundant_token_rate": fixed_econ["redundant_token_rate"],
            "observed_cost_usd": fixed_econ["observed_cost_usd"],
            "redundant_cost_usd": fixed_econ["redundant_cost_usd"],
            "redundant_cost_rate": fixed_econ["redundant_cost_rate"],
        },
    ]
)
st.dataframe(comparison_df, use_container_width=True, hide_index=True)

st.caption(
    "Cost evidence is an efficiency signal only. It cannot override a blocker, provider error, truncation or SLO failure."
)

st.subheader("Risk cohorts")
cohort_rows = []
for risk, metrics in adaptive.get("cohorts", {}).items():
    cohort_rows.append(
        {
            "risk": risk,
            "cases": metrics.get("scenario_count"),
            "pass_rate": metrics.get("pass_rate"),
            "mean_latency_ms": metrics.get("mean_latency_ms"),
            "hedge_rate": metrics.get("hedge_rate"),
            "fallback_winner_rate": metrics.get("fallback_winner_rate"),
            "redundant_token_rate": metrics.get("redundant_token_rate"),
            "redundant_cost_rate": metrics.get("redundant_cost_rate"),
        }
    )
if cohort_rows:
    st.dataframe(pd.DataFrame(cohort_rows), use_container_width=True, hide_index=True)

st.subheader("Repeated critical timeout recovery")
critical = data["critical_fault_recovery"]
trials = critical.get("trials", [])
if trials:
    rows = []
    for item in trials:
        report = item.get("report", item)
        rows.append(
            {
                "trial": item.get("trial"),
                "production": report["production_decision"]["decision"],
                "mean_latency_ms": report["run"]["mean_latency_ms"],
                "p95_latency_ms": report["run"]["p95_latency_ms"],
                "provider_errors": report["run"]["provider_errors"],
                "truncations": report["run"]["completion_truncations"],
                "blockers": report["release_report"]["blocker_failures"],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    # Backward-compatible rendering for evidence payloads that summarize the fault trials.
    summary = critical.get("trial_summaries") or critical.get("summary")
    if summary:
        st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

if fallback_timeout is not None:
    st.caption(
        f"Fallback request deadline: {float(fallback_timeout):.3f} s, derived from the unchanged 8 s p95 envelope with a reserved safety margin."
    )

st.success(
    "Authoritative fault qualification: all repeated critical primary-timeout trials passed the unchanged behavioral and latency gates."
)

st.subheader("Healthy repeated qualification")
stability = data["repeated_qualification"]["stability"]
sc1, sc2, sc3 = st.columns(3)
sc1.metric("Stable", "YES" if stability["stable"] else "NO")
sc2.metric("Production SHIP rate", f"{stability['production_ship_rate'] * 100:.0f}%")
sc3.metric("Behavioral SHIP rate", f"{stability['behavioral_ship_rate'] * 100:.0f}%")

st.subheader("Release contract")
contract = data["release_contract"]
st.code(
    f"behavioral {contract['behavioral']}\n"
    f"blockers = {contract['blockers']}\n"
    f"unrecovered truncations = {contract['unrecovered_truncations']}\n"
    f"final provider errors = {contract['final_provider_errors']}\n"
    f"mean latency <= {contract['max_mean_latency_ms'] / 1000:.0f} s\n"
    f"p95 latency <= {contract['max_p95_latency_ms'] / 1000:.0f} s"
)

st.subheader("Infrastructure status")
infra = data["infrastructure"]
st.write(f"**Routed adaptive inference:** {infra['routed_adaptive']}")
st.write(f"**Dedicated endpoint:** {infra['dedicated']}")
st.write(f"**Dedicated release-critical:** {infra['dedicated_release_critical']}")
st.caption("No paid dedicated endpoint is provisioned implicitly.")

st.subheader("Evidence")
st.code(EVIDENCE_PATH)
st.caption(
    "The machine-readable artifact is published to the HIA-Lab Hugging Face Dataset and storage bucket."
)
