from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"

st.set_page_config(page_title="Hedged Requests | HIA-Lab", page_icon="⚡", layout="wide")
st.title("Phase 1.7 — Hedged Requests & Infrastructure Bakeoff")
st.caption("Parallel recovery · hedge-threshold bakeoff · unchanged production SLOs")


def _load(filename: str):
    try:
        path = hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=filename)
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, HfHubHTTPError):
        return None


data = _load("runs/hedged_requests_latest.json")
if not data:
    st.info("No Phase 1.7 hedged-request evidence has been published yet.")
    st.stop()

exec_decision = data["executive_decision"]
thresholds = data["threshold_bakeoff"]
faults = data["fault_recovery"]
stability = data["extended_qualification"]["stability"]
infra = data["infrastructure_bakeoff"]

if exec_decision["decision"] == "SHIP":
    st.success("Executive Phase 1.7 decision: SHIP")
else:
    st.error("Executive Phase 1.7 decision: HOLD — " + "; ".join(exec_decision["reasons"]))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Selected hedge delay", f"{thresholds['selected_ms'] / 1000:.1f} s")
c2.metric("Primary", data["routes"]["primary"])
c3.metric("Fallback", data["routes"]["fallback"])
c4.metric("Healthy worst p95", f"{stability['worst_trial_p95_ms'] / 1000:.2f} s")

st.subheader("Hedge-threshold bakeoff")
rows = []
for delay, entry in thresholds["reports"].items():
    summary = entry["summary"]
    rows.append(
        {
            "hedge_delay_ms": int(delay),
            "behavioral": summary["behavioral"],
            "production": summary["production"],
            "mean_latency_s": round(summary["mean_latency_ms"] / 1000, 3),
            "p95_latency_s": round(summary["p95_latency_ms"] / 1000, 3),
            "hedge_rate": summary["hedge_rate"],
            "fallback_winner_rate": summary["fallback_winner_rate"],
            "average_attempts": summary["average_attempts"],
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption(
    "The 1.5 s threshold was selected because it produced the lowest eligible p95 in this run while "
    "hedging only 8.33% of healthy requests. Lower delays duplicated substantially more work."
)

st.subheader("Injected-fault recovery")
fault_rows = []
for name in ["primary_timeout", "primary_truncation", "simultaneous_degradation"]:
    entry = faults[name]
    summary = entry["summary"]
    fault_rows.append(
        {
            "case": name,
            "behavioral": summary["behavioral"],
            "production": summary["production"],
            "mean_latency_s": round(summary["mean_latency_ms"] / 1000, 3)
            if summary["mean_latency_ms"] is not None
            else None,
            "p95_latency_s": round(summary["p95_latency_ms"] / 1000, 3)
            if summary["p95_latency_ms"] is not None
            else None,
            "hedge_rate": summary["hedge_rate"],
            "fallback_winner_rate": summary["fallback_winner_rate"],
            "passed": entry.get("passed", entry.get("failed_closed")),
        }
    )
st.dataframe(pd.DataFrame(fault_rows), use_container_width=True, hide_index=True)

r1, r2, r3 = st.columns(3)
timeout = faults["primary_timeout"]["summary"]
r1.metric("Timeout recovery mean", f"{timeout['mean_latency_ms'] / 1000:.3f} s")
r2.metric("Timeout recovery p95", f"{timeout['p95_latency_ms'] / 1000:.3f} s")
r3.metric("Timeout fallback winner", f"{timeout['fallback_winner_rate']:.0%}")

st.subheader("Extended healthy-route qualification")
st.write(
    {
        "trials": stability["trials"],
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
            "mean_latency_s": round(trial["run"]["mean_latency_ms"] / 1000, 3),
            "p95_latency_s": round(trial["run"]["p95_latency_ms"] / 1000, 3),
            "hedge_rate": trial["hedging"]["hedge_rate"],
            "fallback_winner_rate": trial["hedging"]["fallback_winner_rate"],
        }
    )
trial_df = pd.DataFrame(trial_rows)
st.dataframe(trial_df, use_container_width=True, hide_index=True)
st.line_chart(trial_df.set_index("trial")[["mean_latency_s", "p95_latency_s"]])

st.subheader("Dedicated infrastructure bakeoff")
st.write(
    {
        "routed_hedged": infra["routed_hedged"]["status"],
        "dedicated": infra["dedicated"]["status"],
        "dedicated_release_critical": infra["dedicated"]["release_critical"],
    }
)
st.info(infra["dedicated"]["reason"])

st.warning(
    "Hedging can duplicate inference work. HIA-Lab therefore publishes hedge rate and attempt provenance in "
    "addition to user-visible latency. Dedicated infrastructure remains non-release-critical until explicitly provisioned."
)
