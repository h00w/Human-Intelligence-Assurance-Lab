from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

from hia.runner import run_demo

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"

st.set_page_config(page_title="Human Intelligence Assurance Lab", page_icon="🧭", layout="wide")
st.title("Human Intelligence Assurance Lab")
st.caption("HIA-Bench v0.1 · Emotional Intelligence Assurance & Production Release Gate")

scenarios, results, report = run_demo()


def _load_dataset_json(filename: str):
    try:
        path = hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=filename)
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, HfHubHTTPError):
        return None


def _ms(value):
    return f"{value:.0f} ms" if value is not None else "n/a"


live = _load_dataset_json("runs/live_eval_latest.json")
bakeoff = _load_dataset_json("runs/model_bakeoff_latest.json")
policy_ablation = _load_dataset_json("runs/policy_ablation_latest.json")
latency = _load_dataset_json("runs/latency_tuning_latest.json")
semantic = _load_dataset_json("runs/semantic_shadow_latest.json")
calibration_report = _load_dataset_json("runs/calibration_report.json")

st.subheader("Latest real-model canary")
if live:
    run = live["run"]
    release = live["release_report"]
    production = live.get("production_decision")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Model", run["model"])
    c2.metric("Behavioral", release["decision"])
    c3.metric("Production", production["decision"] if production else "legacy")
    c4.metric("Pass rate", f"{release['pass_rate']:.1%}")
    c5.metric("Mean latency", _ms(run.get("mean_latency_ms")))
    cost = run.get("estimated_cost_usd")
    c6.metric("Est. run cost", f"${cost:.5f}" if cost is not None else "n/a")

    if production:
        message = "; ".join(production["reasons"])
        if production["decision"] == "SHIP":
            st.success("Production SHIP — behavioral and operational gates passed.")
        elif production["decision"] == "INVESTIGATE":
            st.warning("Production INVESTIGATE — " + message)
        else:
            st.error("Production HOLD — " + message)

    if live.get("lineage"):
        st.caption(
            f"Run lineage: `{live['lineage']['fingerprint']}` · evaluator "
            f"{live['lineage']['evaluator_version']} · prompt {live['lineage']['prompt_version']}"
        )

    operational = live.get("operational_report")
    if operational:
        o1, o2, o3 = st.columns(3)
        o1.metric("p95 latency", _ms(run.get("p95_latency_ms")))
        o2.metric("Provider errors", run.get("provider_errors", 0))
        o3.metric("Truncations", run.get("completion_truncations", 0))
        if operational["passed"]:
            st.success("Operational regression gate passed.")
        else:
            st.warning("Operational regression evidence: " + "; ".join(operational["reasons"]))

    live_domains = pd.DataFrame(
        [{"domain": key, "pass_rate": value} for key, value in release["domain_pass_rates"].items()]
    ).set_index("domain")
    st.bar_chart(live_domains)

    with st.expander("Real-model evidence"):
        evidence_rows = [
            {
                "scenario": row["scenario"]["id"],
                "domain": row["scenario"]["domain"],
                "risk": row["scenario"]["risk_level"],
                "passed": row["evaluation"]["passed"],
                "latency_ms": row["generation"]["latency_ms"],
                "violations": ", ".join(row["evaluation"]["violations"]),
                "response": row["generation"]["text"],
            }
            for row in live["evidence"]
        ]
        st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True)
else:
    st.info("No published real-model run yet. The deterministic reference benchmark remains available below.")

st.subheader("Phase 1.2.1 · Live model bakeoff")
if bakeoff:
    baseline = bakeoff["baseline"]
    candidate = bakeoff["candidate"]
    comparison = bakeoff["comparison"]
    st.markdown(f"**Safety-first winner:** `{comparison['winner']}` — {'; '.join(comparison['rationale'])}")
    rows = []
    for role, candidate_report in (("baseline", baseline), ("candidate", candidate)):
        candidate_run = candidate_report["run"]
        candidate_release = candidate_report["release_report"]
        rows.append(
            {
                "role": role,
                "model": candidate_run["model"],
                "behavioral": candidate_release["decision"],
                "production": candidate_report.get("production_decision", {}).get("decision", "legacy"),
                "pass_rate": candidate_release["pass_rate"],
                "blockers": candidate_release["blocker_failures"],
                "truncations": candidate_run.get("completion_truncations", 0),
                "mean_latency_ms": candidate_run.get("mean_latency_ms"),
                "p95_latency_ms": candidate_run.get("p95_latency_ms"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No two-model bakeoff has been published yet.")

st.subheader("Phase 1.2.2 · Executable policy ablation")
if policy_ablation:
    comparison = policy_ablation["comparison"]
    st.markdown(f"**Policy winner:** `{comparison['winner']}` — {'; '.join(comparison['rationale'])}")
    rows = []
    for policy_name, key in (("generic", "generic_policy"), ("risk-aware", "risk_aware_policy")):
        candidate_report = policy_ablation[key]
        candidate_run = candidate_report["run"]
        candidate_release = candidate_report["release_report"]
        rows.append(
            {
                "policy": policy_name,
                "behavioral": candidate_release["decision"],
                "production": candidate_report.get("production_decision", {}).get("decision", "legacy"),
                "pass_rate": candidate_release["pass_rate"],
                "blockers": candidate_release["blocker_failures"],
                "truncations": candidate_run.get("completion_truncations", 0),
                "mean_latency_ms": candidate_run.get("mean_latency_ms"),
                "p95_latency_ms": candidate_run.get("p95_latency_ms"),
                "lineage": candidate_report["lineage"]["fingerprint"],
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No executable-policy ablation has been published yet.")

st.subheader("Phase 1.3 · Production SLO closure")
if latency:
    selection = latency["selection"]
    winner = selection.get("winner")
    if selection["decision"] == "SHIP":
        st.success(
            f"Production SHIP — selected `{winner}`. "
            + "; ".join(selection.get("rationale", []))
        )
    else:
        st.warning("No generation profile satisfied every production gate.")

    profile_rows = []
    for name, profile in latency["profiles"].items():
        profile_report = profile["report"]
        profile_run = profile_report["run"]
        profile_release = profile_report["release_report"]
        production = profile_report["production_decision"]
        profile_rows.append(
            {
                "profile": name,
                "selected": name == winner,
                "max_tokens": profile["generation"]["max_tokens"],
                "behavioral": profile_release["decision"],
                "production": production["decision"],
                "pass_rate": profile_release["pass_rate"],
                "blockers": profile_release["blocker_failures"],
                "provider_errors": profile_run.get("provider_errors", 0),
                "truncations": profile_run.get("completion_truncations", 0),
                "mean_latency_ms": profile_run.get("mean_latency_ms"),
                "p95_latency_ms": profile_run.get("p95_latency_ms"),
                "tokens": profile_run.get("total_tokens"),
            }
        )
    st.dataframe(pd.DataFrame(profile_rows), use_container_width=True, hide_index=True)

    if winner:
        winner_run = latency["profiles"][winner]["report"]["run"]
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Selected profile", winner)
        p2.metric("Mean latency", _ms(winner_run.get("mean_latency_ms")))
        p3.metric("p95 latency", _ms(winner_run.get("p95_latency_ms")))
        p4.metric("Production SLO", "≤ 8,000 ms p95")
    st.caption(
        "Generation budget is treated as an experiment, not an assumed optimization. "
        "A faster profile cannot compensate for a behavioral blocker, provider error, or truncation."
    )
else:
    st.info("No Phase 1.3 latency-tuning evidence has been published yet.")

st.subheader("Semantic quality calibration")
if semantic:
    calibration = semantic.get("calibration", {})
    scores = semantic.get("scores", [])
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Judge mode", semantic.get("mode", "shadow").upper())
    s2.metric("Judge model", semantic.get("judge_model", "n/a"))
    s3.metric("Review queue", calibration.get("review_queue_size", len(scores)))
    s4.metric("Calibration", calibration.get("status", "UNKNOWN"))
    st.warning(
        "Semantic judge results remain shadow evidence until independent human review meets "
        "the configured agreement and critical-failure recall thresholds."
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
        "Semantic shadow evaluation is intentionally manual. Run it with an independent judge model to create "
        "the 24-sample human-review queue."
    )

if calibration_report:
    scored = calibration_report["report"]
    st.markdown("**Human calibration report**")
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Reviewed", scored["sample_count"])
    h2.metric("Agreement", f"{scored['agreement']:.1%}")
    h3.metric("Cohen's κ", f"{scored['cohen_kappa']:.3f}")
    h4.metric("Critical recall", f"{scored['critical_recall']:.1%}")
    if scored["calibrated"]:
        st.success("Semantic judge calibration contract passed.")
    else:
        st.warning("Semantic judge remains shadow-only; calibration contract has not passed.")

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

st.subheader("Reference domain pass rates")
domain_df = pd.DataFrame(
    [{"domain": key, "pass_rate": value} for key, value in report.domain_pass_rates.items()]
).set_index("domain")
st.bar_chart(domain_df)

st.subheader("HIA-Bench scenario explorer")
by_result = {result.scenario_id: result for result in results}
rows = [
    {
        "id": scenario.id,
        "domain": scenario.domain,
        "risk": scenario.risk_level,
        "severity": scenario.release_severity,
        "passed": by_result[scenario.id].passed,
        "violations": ", ".join(by_result[scenario.id].violations),
        "prompt": scenario.input.user_message,
    }
    for scenario in scenarios
]
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.info(
    "HIA-Bench uses synthetic scenarios and auditable checks. Emotional-state fields are hypotheses, not clinical "
    "labels or ground truth. Live model and semantic-judge results are evidence for this benchmark only."
)
