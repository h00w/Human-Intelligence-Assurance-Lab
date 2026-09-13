from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs" / "hedged_requests_latest.json"

st.set_page_config(page_title="HIA-Lab — Hedged Requests", page_icon="⚡", layout="wide")
st.title("Phase 1.7 — Hedged Requests")
st.caption("Parallel primary/fallback qualification with unchanged production SLOs.")

if not RUN.exists():
    st.info("Phase 1.7 live evidence has not been published yet.")
    st.stop()

payload = json.loads(RUN.read_text(encoding="utf-8"))
executive = payload.get("executive_decision", {})
thresholds = payload.get("threshold_bakeoff", {})
faults = payload.get("fault_recovery", {})
extended = payload.get("extended_qualification", {})
infra = payload.get("infrastructure_bakeoff", {})

st.metric("Executive decision", executive.get("decision", "UNKNOWN"))
st.write("Selected hedge delay:", f"{thresholds.get('selected_ms', 'n/a')} ms")

rows = []
for delay, entry in thresholds.get("reports", {}).items():
    summary = entry.get("summary", {})
    rows.append({"hedge_delay_ms": delay, **summary})
if rows:
    st.subheader("Hedge-threshold bakeoff")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Fault recovery")
fault_rows = []
for name, entry in faults.items():
    if name == "simultaneous_degradation":
        summary = entry.get("summary", {})
        summary["passed"] = entry.get("failed_closed")
    else:
        summary = entry.get("summary", {})
        summary["passed"] = entry.get("passed")
    fault_rows.append({"case": name, **summary})
st.dataframe(pd.DataFrame(fault_rows), use_container_width=True, hide_index=True)

st.subheader("Repeated qualification")
st.json(extended.get("stability", {}), expanded=False)

st.subheader("Infrastructure bakeoff")
st.json(infra, expanded=False)

st.warning(
    "A dedicated endpoint is not provisioned implicitly. Routed hedging is release-critical; "
    "dedicated infrastructure remains non-release-critical until explicitly configured."
)
