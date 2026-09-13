from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"

st.set_page_config(page_title="Fault Injection | HIA-Lab", page_icon="🧪", layout="wide")
st.title("Phase 1.6 — Fault Injection & Infrastructure Qualification")
st.caption("Live fallback exercise · fail-closed degradation · extended qualification")


def _load(filename: str):
    try:
        path = hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=filename)
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, HfHubHTTPError):
        return None


data = _load("runs/fault_injection_latest.json")
if not data:
    st.info("No Phase 1.6 fault-injection evidence has been published yet.")
    st.stop()

faults = data["fault_injection"]
timeout_case = faults["primary_timeout"]
trunc_case = faults["primary_truncation"]
dual_case = faults["simultaneous_degradation"]
stability = data["extended_qualification"]["stability"]
exec_decision = data["executive_decision"]
infra = data["infrastructure_comparison"]

if exec_decision["decision"] == "SHIP":
    st.success("Executive Phase 1.6 decision: SHIP")
else:
    st.error("Executive Phase 1.6 decision: HOLD — " + "; ".join(exec_decision["reasons"]))

st.markdown(
    "The authoritative run charges the full **4.0 s primary timeout budget** before fallback. "
    "The earlier zero-cost timeout experiment is superseded."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Primary route", data["routes"]["primary"])
c2.metric("Fallback route", data["routes"]["fallback"])
c3.metric("Healthy trials", stability["trials"])
c4.metric("Healthy worst p95", f"{stability['worst_trial_p95_ms'] / 1000:.2f} s")

st.subheader("Injected-fault qualification")
rows = []
for label, case in [
    ("Primary timeout", timeout_case),
    ("Primary truncation", trunc_case),
    ("Dual-provider degradation", dual_case),
]:
    report = case["report"]
    run = report["run"]
    rows.append(
        {
            "fault": label,
            "primary_fault": case["primary_fault"],
            "fallback_fault": case["fallback_fault"],
            "failover_rate": case["failover_rate"],
            "behavioral": report["release_report"]["decision"],
            "production": report["production_decision"]["decision"],
            "mean_latency_s": round(run["mean_latency_ms"] / 1000, 3)
            if run.get("mean_latency_ms") is not None
            else None,
            "p95_latency_s": round(run["p95_latency_ms"] / 1000, 3)
            if run.get("p95_latency_ms") is not None
            else None,
            "provider_errors": run["provider_errors"],
            "truncations": run["completion_truncations"],
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

r1, r2, r3 = st.columns(3)
timeout_prod = timeout_case["report"]["production_decision"]
r1.metric("Timeout recovery p95", f"{timeout_case['report']['run']['p95_latency_ms'] / 1000:.2f} s")
r2.metric("Timeout recovery mean", f"{timeout_case['report']['run']['mean_latency_ms'] / 1000:.2f} s")
r3.metric("Timeout production verdict", timeout_prod["decision"])
st.caption("Timeout verdict rationale: " + "; ".join(timeout_prod["reasons"]))

r4, r5, r6 = st.columns(3)
r4.metric("Truncation recovery", trunc_case["report"]["production_decision"]["decision"])
r5.metric("Truncation recovery p95", f"{trunc_case['report']['run']['p95_latency_ms'] / 1000:.2f} s")
r6.metric("Dual degradation", dual_case["report"]["production_decision"]["decision"])

st.subheader("Extended healthy-route qualification")
st.write(
    {
        "production_ship_rate": stability["production_ship_rate"],
        "behavioral_ship_rate": stability["behavioral_ship_rate"],
        "blocker_trial_rate": stability["blocker_trial_rate"],
        "provider_error_trial_rate": stability["provider_error_trial_rate"],
        "truncation_trial_rate": stability["truncation_trial_rate"],
        "mean_latency_s": round(stability["mean_latency_ms"] / 1000, 3),
        "median_trial_p95_s": round(stability["median_trial_p95_ms"] / 1000, 3),
        "worst_trial_p95_s": round(stability["worst_trial_p95_ms"] / 1000, 3),
        "stable": stability["stable"],
    }
)

trial_rows = []
for trial in data["extended_qualification"]["trials"]:
    trial_rows.append(
        {
            "trial": trial["trial"],
            "behavioral": trial["release_report"]["decision"],
            "production": trial["production_decision"]["decision"],
            "pass_rate": trial["release_report"]["pass_rate"],
            "mean_latency_s": round(trial["run"]["mean_latency_ms"] / 1000, 3),
            "p95_latency_s": round(trial["run"]["p95_latency_ms"] / 1000, 3),
            "failover_rate": trial["resilience"]["failover_rate"],
        }
    )
trial_df = pd.DataFrame(trial_rows)
st.dataframe(trial_df, use_container_width=True, hide_index=True)
st.line_chart(trial_df.set_index("trial")[["mean_latency_s", "p95_latency_s"]])

st.subheader("Infrastructure comparison")
st.write(
    {
        "routed_inference": "MEASURED",
        "dedicated_endpoint": infra["dedicated"]["status"],
        "dedicated_release_critical": exec_decision["dedicated_infrastructure_release_critical"],
    }
)
st.info(infra["dedicated"]["reason"])

st.warning(
    "Phase 1.6 remains HOLD because the forced 4-second timeout plus real fallback exceeds the 5-second "
    "mean-latency SLO, even though p95 remains below 8 seconds. The SLO is intentionally not relaxed."
)
