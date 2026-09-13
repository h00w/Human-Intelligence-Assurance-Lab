from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"

st.set_page_config(page_title="Provider Resilience | HIA-Lab", page_icon="🛡️", layout="wide")
st.title("Phase 1.5 — Provider Resilience")
st.caption("Provider-route bakeoff · Bounded critical responses · Deadline-aware qualification")


def _load(filename: str):
    try:
        path = hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=filename)
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, HfHubHTTPError):
        return None


data = _load("runs/provider_resilience_latest.json")
if not data:
    st.info("No Phase 1.5 provider-resilience evidence has been published yet.")
    st.stop()

selection = data["provider_bakeoff"]["selection"]
stability = data["qualification"]["stability"]
decision = data["executive_decision"]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Executive decision", decision["decision"])
c2.metric("Provider winner", selection.get("winner") or "none")
c3.metric("Production SHIP rate", f"{stability['production_ship_rate']:.0%}")
c4.metric("Behavioral SHIP rate", f"{stability['behavioral_ship_rate']:.0%}")
c5.metric("Worst trial p95", f"{stability['worst_trial_p95_ms'] / 1000:.2f} s")

if decision["decision"] == "SHIP":
    st.success("Phase 1.5 SHIP — " + "; ".join(decision["reasons"]))
else:
    st.error(f"Phase 1.5 {decision['decision']} — " + "; ".join(decision["reasons"]))

st.subheader("Provider-route bakeoff")
provider_rows = []
for provider, report in data["provider_bakeoff"]["reports"].items():
    run = report["run"]
    release = report["release_report"]
    provider_rows.append(
        {
            "provider": provider,
            "behavioral": release["decision"],
            "production": report["production_decision"]["decision"],
            "pass_rate": release["pass_rate"],
            "blockers": release["blocker_failures"],
            "provider_errors": run["provider_errors"],
            "truncations": run["completion_truncations"],
            "mean_latency_s": round(run["mean_latency_ms"] / 1000, 2),
            "p95_latency_s": round(run["p95_latency_ms"] / 1000, 2),
        }
    )
provider_df = pd.DataFrame(provider_rows).sort_values("p95_latency_s")
st.dataframe(provider_df, use_container_width=True, hide_index=True)
st.bar_chart(provider_df.set_index("provider")[["mean_latency_s", "p95_latency_s"]])
st.caption("Provider eligibility requires behavioral SHIP, zero blockers/errors/truncations, and p95 <=8 s.")

st.subheader("Deadline-aware route")
route = data["failover"]
r1, r2, r3 = st.columns(3)
r1.metric("Route order", " → ".join(route["route_order"]))
r2.metric("Primary timeout", f"{route['primary_timeout_s']:.0f} s")
r3.metric("Fallback timeout", f"{route['fallback_timeout_s']:.0f} s")
st.caption(route["note"])

st.subheader("Repeated qualification")
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

trial_rows = []
for trial in data["qualification"]["trials"]:
    run = trial["run"]
    resilience = trial.get("resilience", {})
    trial_rows.append(
        {
            "trial": trial["trial"],
            "behavioral": trial["release_report"]["decision"],
            "production": trial["production_decision"]["decision"],
            "pass_rate": trial["release_report"]["pass_rate"],
            "blockers": trial["release_report"]["blocker_failures"],
            "provider_errors": run["provider_errors"],
            "truncations": run["completion_truncations"],
            "mean_latency_s": round(run["mean_latency_ms"] / 1000, 2),
            "p95_latency_s": round(run["p95_latency_ms"] / 1000, 2),
            "failover_rate": resilience.get("failover_rate", 0.0),
            "avg_attempts": resilience.get("average_attempts", 0.0),
        }
    )
trial_df = pd.DataFrame(trial_rows)
st.dataframe(trial_df, use_container_width=True, hide_index=True)
st.line_chart(trial_df.set_index("trial")[["mean_latency_s", "p95_latency_s"]])

f1, f2, f3 = st.columns(3)
f1.metric("Blocker trial rate", f"{stability['blocker_trial_rate']:.0%}")
f2.metric("Provider-error trial rate", f"{stability['provider_error_trial_rate']:.0%}")
f3.metric("Truncation trial rate", f"{stability['truncation_trial_rate']:.0%}")

live_failover = sum(row["failover_rate"] for row in trial_rows)
if live_failover == 0:
    st.info(
        "The fallback path was configured and unit-tested, but was not exercised in this live five-trial run: "
        "the Nscale primary completed all 60 qualification requests before the 4-second deadline."
    )
else:
    st.success("Live failover was exercised during qualification; inspect the evidence rows for route attempts.")

st.subheader("Critical-response control")
st.json(data["bounded_policy"])
st.caption(
    "Critical cases front-load the required safety boundary and next action, target a complete <=120-word response, "
    "and suppress speculative differential-diagnosis lists in critical wellness cases."
)

st.info(
    "This SHIP result is scoped to the evaluated model, provider routes, policy, generation parameters, and "
    "synthetic 12-case HIA canary. The live run did not inject a primary-route failure, so fallback recovery remains "
    "unit-tested rather than live fault-injection evidence."
)
