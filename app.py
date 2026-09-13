from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

from hia.runner import run_demo

st.set_page_config(page_title="Human Intelligence Assurance Lab", page_icon="🧭", layout="wide")
st.title("Human Intelligence Assurance Lab")
st.caption("HIA-Bench v0.1 · Emotional Intelligence Assurance & Release Gate")

scenarios, results, report = run_demo()


def _load_dataset_json(filename: str):
    try:
        path = hf_hub_download(
            repo_id="h0000w/Human-Intelligence-Assurance-Lab",
            repo_type="dataset",
            filename=filename,
        )
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, HfHubHTTPError):
        return None


live = _load_dataset_json("runs/live_eval_latest.json")
bakeoff = _load_dataset_json("runs/model_bakeoff_latest.json")
policy_ablation = _load_dataset_json("runs/policy_ablation_latest.json")
semantic = _load_dataset_json("runs/semantic_shadow_latest.json")

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

    if live.get("lineage"):
        st.caption(
            f"Run lineage: `{live['lineage']['fingerprint']}` · evaluator "
            f"{live['lineage']['evaluator_version']} · prompt {live['lineage']['prompt_version']}"
        )

    operational = live.get("operational_report")
    if operational:
        if operational["passed"]:
            st.success("Operational regression gate passed.")
        else:
            st.warning("Operational regression evidence: " + "; ".join(operational["reasons"]))
        o1, o2, o3 = st.columns(3)
        p95 = run.get("p95_latency_ms")
        o1.metric("p95 latency", f"{p95:.0f} ms" if p95 is not None else "n/a")
        o2.metric("Provider errors", run.get("provider_errors", 0))
        o3.metric("Truncations", run.get("completion_truncations", 0))

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

st.subheader("Phase 1.2.1 live model bakeoff")
if bakeoff:
    baseline = bakeoff["baseline"]
    candidate = bakeoff["candidate"]
    comparison = bakeoff["comparison"]
    b_run, b_release = baseline["run"], baseline["release_report"]
    c_run, c_release = candidate["run"], candidate["release_report"]

    st.markdown(f"**Safety-first winner:** `{comparison['winner']}` — {'; '.join(comparison['rationale'])}")
    compare_df = pd.DataFrame(
        [
            {
                "role": "baseline",
                "model": b_run["model"],
                "decision": b_release["decision"],
                "pass_rate": b_release["pass_rate"],
                "blockers": b_release["blocker_failures"],
                "truncations": b_run.get("completion_truncations", 0),
                "mean_latency_ms": b_run.get("mean_latency_ms"),
                "p95_latency_ms": b_run.get("p95_latency_ms"),
            },
            {
                "role": "candidate",
                "model": c_run["model"],
                "decision": c_release["decision"],
                "pass_rate": c_release["pass_rate"],
                "blockers": c_release["blocker_failures"],
                "truncations": c_run.get("completion_truncations", 0),
                "mean_latency_ms": c_run.get("mean_latency_ms"),
                "p95_latency_ms": c_run.get("p95_latency_ms"),
            },
        ]
    )
    st.dataframe(compare_df, use_container_width=True, hide_index=True)
    st.caption(
        "Comparison is lexicographic: blocker failures and release status dominate quality, latency, and cost. "
        "Semantic scores are excluded until human calibration requirements are met."
    )
else:
    st.info("No two-model bakeoff has been published yet.")

st.subheader("Phase 1.2.2 executable policy ablation")
if policy_ablation:
    generic = policy_ablation["generic_policy"]
    aware = policy_ablation["risk_aware_policy"]
    comparison = policy_ablation["comparison"]
    g_run, g_release = generic["run"], generic["release_report"]
    a_run, a_release = aware["run"], aware["release_report"]
    st.markdown(f"**Policy winner:** `{comparison['winner']}` — {'; '.join(comparison['rationale'])}")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "policy": "generic",
                    "decision": g_release["decision"],
                    "pass_rate": g_release["pass_rate"],
                    "blockers": g_release["blocker_failures"],
                    "truncations": g_run.get("completion_truncations", 0),
                    "mean_latency_ms": g_run.get("mean_latency_ms"),
                    "lineage": generic["lineage"]["fingerprint"],
                },
                {
                    "policy": "risk-aware",
                    "decision": a_release["decision"],
                    "pass_rate": a_release["pass_rate"],
                    "blockers": a_release["blocker_failures"],
                    "truncations": a_run.get("completion_truncations", 0),
                    "mean_latency_ms": a_run.get("mean_latency_ms"),
                    "lineage": aware["lineage"]["fingerprint"],
                },
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Model, provider, benchmark, and generation parameters are held constant. Only the executable policy "
        "overlay changes, so this section isolates orchestration effects."
    )
else:
    st.info("No executable-policy ablation has been published yet.")

st.subheader("Phase 1.2 semantic quality calibration")
if semantic:
    calibration = semantic.get("calibration", {})
    scores = semantic.get("scores", [])
    s1, s2, s3 = st.columns(3)
    s1.metric("Judge mode", semantic.get("mode", "shadow").upper())
    s2.metric("Judge model", semantic.get("judge_model", "n/a"))
    s3.metric("Calibration", calibration.get("status", "UNKNOWN"))
    st.warning(
        "Semantic judge results are shadow evidence and are not release-critical until independent "
        "human-review calibration meets the configured agreement thresholds."
    )
    if scores:
        semantic_rows = pd.DataFrame(
            [
                {
                    "scenario": row["scenario_id"],
                    "domain": row["domain"],
                    "risk": row["risk_level"],
                    "overall": row["semantic"]["overall"],
                    "judge_pass": row["semantic"]["pass_label"],
                    "rationale": row["semantic"]["rationale"],
                }
                for row in scores
            ]
        )
        st.dataframe(semantic_rows, use_container_width=True, hide_index=True)
else:
    st.info(
        "Semantic judge has not been run yet. Trigger the manual Semantic Shadow Evaluation workflow with "
        "an independent judge model; HIA-Lab will generate semantic evidence and a human-review queue."
    )

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
    "not clinical labels or ground truth. Live model and semantic-judge results are evidence for this "
    "benchmark only."
)
