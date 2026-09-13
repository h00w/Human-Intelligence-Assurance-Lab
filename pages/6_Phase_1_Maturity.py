from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from huggingface_hub import hf_hub_download

from hia.v1_readiness import assess_v1_readiness

DATASET = "h0000w/Human-Intelligence-Assurance-Lab"


@st.cache_data(ttl=300)
def load_json(path: str):
    try:
        local = hf_hub_download(DATASET, path, repo_type="dataset")
        return json.loads(Path(local).read_text(encoding="utf-8"))
    except Exception:  # public dashboard should degrade to explicit missing evidence
        return None


st.set_page_config(page_title="Phase 1 Maturity", page_icon="🧱", layout="wide")
st.title("🧱 Phase 1 Maturity & v1.0 Readiness")
st.caption("A fail-closed view of the remaining evidence required after Phase 1.8 SHIP.")

adaptive = load_json("runs/adaptive_hedging_latest.json")
calibration = load_json("runs/calibration_report.json")
long_window = load_json("runs/long_window_latest.json")
dedicated = load_json("runs/dedicated_qualification_latest.json")

phase18_ship = bool(adaptive and adaptive.get("executive_decision", {}).get("decision") == "SHIP")
human_ready = bool(calibration and calibration.get("semantic_release_critical") is True)
long_ready = bool(long_window and long_window.get("report", {}).get("ready") is True)
dedicated_status = (dedicated or {}).get("status", "NOT_CONFIGURED")
readiness = assess_v1_readiness(
    phase18_ship=phase18_ship,
    human_calibrated=human_ready,
    long_window_ready=long_ready,
    dedicated_status=dedicated_status,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Phase 1.8", "SHIP" if phase18_ship else "MISSING/HOLD")
c2.metric("Human calibration", "PASS" if human_ready else "BLOCKED")
c3.metric("Long-window", (long_window or {}).get("status", "WAITING"))
c4.metric("Dedicated", dedicated_status)

st.subheader(f"v1.0 readiness: {readiness.status}")
if readiness.ready:
    st.success("All Phase 1 maturity gates are satisfied. The repository is eligible for v1.0 release packaging.")
else:
    st.warning("Phase 1.8 remains valid SHIP evidence, but Phase 1 v1.0 is not mature yet.")
    for blocker in readiness.blockers:
        st.write(f"- {blocker}")

st.subheader("Human semantic calibration")
st.write("Release threshold: ≥20 resolved samples, ≥2 independent reviewers/sample, inter-reviewer κ ≥0.70, judge-vs-human κ ≥0.70, critical-failure recall ≥0.95.")
if calibration:
    st.json({
        "reviewer_count": calibration.get("reviewer_count"),
        "reviewed_samples": calibration.get("reviewed_samples"),
        "unresolved_samples": calibration.get("unresolved_samples"),
        "inter_reviewer_kappa": calibration.get("inter_reviewer_kappa"),
        "semantic_release_critical": calibration.get("semantic_release_critical"),
    })
else:
    st.info("No qualifying independent human calibration artifact is published yet. Semantic judging stays shadow-only.")

st.subheader("Long-window qualification")
if long_window:
    st.json(long_window.get("report", {}))
else:
    st.info("No time-separated series is mature yet. The weekly qualification workflow will archive dated snapshots; insufficient history is WAITING, not SHIP.")

st.subheader("Dedicated infrastructure")
if dedicated:
    st.json({"status": dedicated.get("status"), "release_critical": dedicated.get("release_critical")})
else:
    st.info("Dedicated endpoint NOT_CONFIGURED. No billable infrastructure is provisioned or contacted automatically.")

st.divider()
st.caption("Phase 1 v1.0 cannot be made green by lowering safety/SLO thresholds, fabricating human labels, or silently provisioning paid infrastructure.")
