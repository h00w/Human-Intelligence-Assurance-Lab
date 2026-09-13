from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download

from hia.runner import run_demo

st.set_page_config(page_title="Human Intelligence Assurance Lab", page_icon="🧭", layout="wide")
st.title("Human Intelligence Assurance Lab")
st.caption("HIA-Bench v0.1 · Emotional Intelligence Assurance & Release Gate")

scenarios, results, report = run_demo()

try:
    live_path = hf_hub_download(
        repo_id="h0000w/Human-Intelligence-Assurance-Lab",
        repo_type="dataset",
        filename="runs/live_eval_latest.json",
    )
    with open(live_path, encoding="utf-8") as handle:
        live = json.load(handle)
except Exception:
    live = None

if live:
    st.subheader("Latest real-model canary")
    run = live["run"]
    release = live["release_report"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Model", run["model"])
    c2.metric("Decision", release["decision"])
    c3.metric("Pass rate", f"{release['pass_rate']:.1%}")
    c4.metric("Mean latency", f"{run['mean_latency_ms']:.0f} ms" if run["mean_latency_ms"] else "n/a")
    cost = run.get("estimated_cost_usd")
    c5.metric("Est. run cost", f"${cost:.5f}" if cost is not None else "n/a")

    live_domains = pd.DataFrame(
        [{"domain": key, "pass_rate": value} for key, value in release["domain_pass_rates"].items()]
    ).set_index("domain")
    st.bar_chart(live_domains)

    with st.expander("Real-model evidence"):
        evidence_rows = []
        for row in live["evidence"]:
            evidence_rows.append(
                {
                    "scenario": row["scenario"]["id"],
                    "domain": row["scenario"]["domain"],
                    "risk": row["scenario"]["risk_level"],
                    "passed": row["evaluation"]["passed"],
                    "latency_ms": row["generation"]["latency_ms"],
                    "violations": ", ".join(row["evaluation"]["violations"]),
                    "response": row["generation"]["text"],
                }
            )
        st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True)
else:
    st.info("No published real-model run yet. The deterministic reference benchmark remains available below.")

st.subheader("Deterministic reference adapter")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Release decision", report.decision)
c2.metric("Pass rate", f"{report.pass_rate:.1%}")
c3.metric("Critical failures", report.critical_failures)
c4.metric("Privacy violations", report.privacy_violations)

if report.decision == "SHIP":
    st.success("SHIP — all hard gates and minimum quality thresholds passed.")
elif report.decision == "INVESTIGATE":
    st.warning("INVESTIGATE — no hard blocker, but quality/regression thresholds are not met.")
else:
    st.error("HOLD — at least one hard safety or privacy gate failed.")

st.write("\n".join(f"- {reason}" for reason in report.reasons))

st.subheader("Reference domain pass rates")
domain_df = pd.DataFrame(
    [{"domain": key, "pass_rate": value} for key, value in report.domain_pass_rates.items()]
).set_index("domain")
st.bar_chart(domain_df)

st.subheader("HIA-Bench scenario explorer")
rows = []
by_result = {result.scenario_id: result for result in results}
for scenario in scenarios:
    result = by_result[scenario.id]
    rows.append(
        {
            "id": scenario.id,
            "domain": scenario.domain,
            "risk": scenario.risk_level,
            "severity": scenario.release_severity,
            "passed": result.passed,
            "violations": ", ".join(result.violations),
            "prompt": scenario.input.user_message,
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.info(
    "HIA-Bench uses synthetic scenarios and auditable checks. Emotional-state fields are hypotheses, "
    "not clinical labels or ground truth. Live model results are evidence for this benchmark only."
)
