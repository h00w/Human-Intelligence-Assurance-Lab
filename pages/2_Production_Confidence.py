from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"

st.set_page_config(page_title="Production Confidence | HIA-Lab", page_icon="📈", layout="wide")
st.title("Phase 1.4 — Production Confidence")
st.caption("Repeated-run stability · Executive assurance · Human-calibration state")


def _load(filename: str):
    try:
        path = hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=filename)
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, HfHubHTTPError):
        return None


study = _load("runs/stability_study_latest.json")
manifest = _load("runs/executive_assurance_manifest.json")
calibration = _load("runs/calibration_report.json")

if not study:
    st.info("No Phase 1.4 repeated-run study has been published yet.")
    st.stop()

stability = study["stability"]
manifest_decision = manifest["decision"] if manifest else {"decision": "UNKNOWN", "reasons": []}

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Executive decision", manifest_decision["decision"])
c2.metric("Trials", stability["trials"])
c3.metric("Production SHIP rate", f"{stability['production_ship_rate']:.0%}")
c4.metric("Behavioral SHIP rate", f"{stability['behavioral_ship_rate']:.0%}")
c5.metric("Worst trial p95", f"{stability['worst_trial_p95_ms'] / 1000:.2f} s")

if stability["stable"]:
    st.success("Repeated-run production-confidence contract passed.")
else:
    st.error("Repeated-run production-confidence contract failed: " + "; ".join(stability["reasons"]))

latency_ci = stability.get("mean_latency_ci95")
p95_ci = stability.get("trial_p95_ci95")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Mean latency", f"{stability['mean_latency_ms'] / 1000:.2f} s")
m2.metric(
    "Mean latency 95% CI",
    f"{latency_ci['lower'] / 1000:.2f}–{latency_ci['upper'] / 1000:.2f} s" if latency_ci else "n/a",
)
m3.metric("Median trial p95", f"{stability['median_trial_p95_ms'] / 1000:.2f} s")
m4.metric(
    "Trial p95 95% CI",
    f"{p95_ci['lower'] / 1000:.2f}–{p95_ci['upper'] / 1000:.2f} s" if p95_ci else "n/a",
)

st.subheader("Trial-by-trial evidence")
rows = []
for trial in study["trials"]:
    rows.append(
        {
            "trial": trial["trial"],
            "behavioral": trial["release_report"]["decision"],
            "production": trial["production_decision"]["decision"],
            "pass_rate": trial["release_report"]["pass_rate"],
            "blockers": trial["release_report"]["blocker_failures"],
            "provider_errors": trial["run"]["provider_errors"],
            "truncations": trial["run"]["completion_truncations"],
            "mean_latency_s": round(trial["run"]["mean_latency_ms"] / 1000, 2),
            "p95_latency_s": round(trial["run"]["p95_latency_ms"] / 1000, 2),
        }
    )
trial_df = pd.DataFrame(rows)
st.dataframe(trial_df, use_container_width=True, hide_index=True)
st.line_chart(trial_df.set_index("trial")[["mean_latency_s", "p95_latency_s"]])

st.subheader("Failure recurrence")
f1, f2, f3 = st.columns(3)
f1.metric("Blocker trial rate", f"{stability['blocker_trial_rate']:.0%}")
f2.metric("Provider-error trial rate", f"{stability['provider_error_trial_rate']:.0%}")
f3.metric("Truncation trial rate", f"{stability['truncation_trial_rate']:.0%}")

failed = []
for trial in study["trials"]:
    for evidence in trial["evidence"]:
        if not evidence["evaluation"]["passed"]:
            failed.append(
                {
                    "trial": trial["trial"],
                    "scenario": evidence["scenario"]["id"],
                    "domain": evidence["scenario"]["domain"],
                    "risk": evidence["scenario"]["risk_level"],
                    "violations": ", ".join(evidence["evaluation"]["violations"]),
                    "finish_reason": evidence["generation"].get("metadata", {}).get("finish_reason"),
                    "latency_s": round(evidence["generation"]["latency_ms"] / 1000, 2),
                    "response": evidence["generation"]["text"],
                }
            )
if failed:
    st.dataframe(pd.DataFrame(failed), use_container_width=True, hide_index=True)
else:
    st.success("No failed scenario evidence in the repeated-run study.")

st.subheader("Executive assurance")
if manifest:
    if manifest_decision["decision"] == "SHIP":
        st.success("Executive SHIP — " + "; ".join(manifest_decision["reasons"]))
    else:
        st.error(f"Executive {manifest_decision['decision']} — " + "; ".join(manifest_decision["reasons"]))
    st.json(
        {
            "candidate": manifest.get("candidate"),
            "semantic_policy": manifest.get("semantic_policy"),
            "limitations": manifest.get("limitations"),
        }
    )

st.subheader("Human semantic calibration")
if calibration:
    report = calibration.get("report", {})
    st.write(
        {
            "reviewed_rows": calibration.get("reviewed_rows"),
            "cohen_kappa": report.get("cohen_kappa"),
            "critical_recall": report.get("critical_recall"),
            "calibrated": report.get("calibrated"),
        }
    )
else:
    st.warning(
        "No independent human calibration report is published yet. Semantic judging therefore remains shadow-only "
        "and is not part of the release-critical decision."
    )

st.info(
    "This evidence is scoped to the evaluated model, provider, executable policy, generation parameters, and "
    "synthetic HIA-Bench canary. It is not a universal safety guarantee or clinical validation."
)
