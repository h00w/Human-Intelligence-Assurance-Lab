import json
from pathlib import Path

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from hia.authoritative import PHASE_1_8_AUTHORITATIVE

DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
EVIDENCE_PATH = "runs/adaptive_hedging_latest.json"
LOCAL_FALLBACK = Path("artifacts/adaptive_hedging_latest.json")

st.set_page_config(page_title="Adaptive Hedging | HIA-Lab", page_icon="⚡", layout="wide")
st.title("Phase 1.8 — Adaptive Hedging & Cost-Aware Routing")
st.caption("Frozen Phase 1.8 release evidence is separated from later operational qualification runs.")


def load_operational_evidence() -> dict | None:
    try:
        path = hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=EVIDENCE_PATH)
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (HfHubHTTPError, OSError, json.JSONDecodeError):
        if LOCAL_FALLBACK.exists():
            return json.loads(LOCAL_FALLBACK.read_text(encoding="utf-8"))
        return None


auth = PHASE_1_8_AUTHORITATIVE
st.success(f"Frozen Phase 1.8 executive decision: {auth['decision']}")
st.caption(
    f"Authoritative GitHub Actions run {auth['workflow_run_id']} / artifact {auth['artifact_id']} / "
    f"source commit `{auth['source_commit']}`. Scope: {auth['scope']}."
)

st.subheader("Authoritative risk-aware hedge schedule")
policy = auth["derived_delays_ms"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Critical", f"{policy['critical']:.0f} ms")
c2.metric("High", f"{policy['high']:.0f} ms")
c3.metric("Medium", f"{policy['medium']:.0f} ms")
c4.metric("Low", f"{policy['low']:.0f} ms")

m1, m2 = st.columns(2)
m1.metric("Adaptive redundant-token rate", f"{auth['adaptive_redundant_token_rate'] * 100:.2f}%")
m2.metric("Fixed 1.5 s redundant-token rate", f"{auth['fixed_redundant_token_rate'] * 100:.2f}%")

st.subheader("Authoritative repeated critical-timeout recovery")
st.dataframe(pd.DataFrame(auth["critical_fault_trials"]), use_container_width=True, hide_index=True)
st.caption(
    f"Fallback request deadline: {auth['fallback_timeout_s']:.3f} s. All three authoritative fault trials SHIPPED under the unchanged production contract."
)

st.divider()
st.subheader("Latest operational adaptive qualification")
data = load_operational_evidence()
if data is None:
    st.info("No current operational adaptive artifact is available.")
else:
    verdict = data.get("executive_decision", {}).get("decision", "UNKNOWN")
    if verdict == "SHIP":
        st.info("Current operational executive decision: SHIP")
    else:
        st.error(
            f"Current operational executive decision: {verdict}. This does not rewrite the frozen Phase 1.8 release; "
            "it is new longitudinal evidence for the Phase 1 maturity gate."
        )

    current_policy = data.get("calibration", {}).get("derived_delays_ms", {})
    if current_policy:
        st.write("**Current derived hedge delays**")
        st.json(current_policy)

    comparison = data.get("comparison", {})
    adaptive = comparison.get("adaptive", {})
    fixed = comparison.get("fixed_1500ms", {})
    if adaptive and fixed:
        adaptive_econ = adaptive.get("economics", {})
        fixed_econ = fixed.get("economics", {})
        st.write("**Current adaptive vs fixed routing economics**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "policy": "Adaptive",
                        "production": adaptive.get("report", {}).get("production_decision", {}).get("decision"),
                        "hedge_rate": adaptive_econ.get("hedge_rate"),
                        "redundant_token_rate": adaptive_econ.get("redundant_token_rate"),
                        "redundant_cost_usd": adaptive_econ.get("redundant_cost_usd"),
                    },
                    {
                        "policy": "Fixed 1.5 s",
                        "production": fixed.get("report", {}).get("production_decision", {}).get("decision"),
                        "hedge_rate": fixed_econ.get("hedge_rate"),
                        "redundant_token_rate": fixed_econ.get("redundant_token_rate"),
                        "redundant_cost_usd": fixed_econ.get("redundant_cost_usd"),
                    },
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    critical = data.get("critical_fault_recovery", {})
    trials = critical.get("trials", [])
    if trials:
        trial_rows = []
        for item in trials:
            report = item.get("report", item)
            trial_rows.append(
                {
                    "trial": item.get("trial"),
                    "production": report.get("production_decision", {}).get("decision"),
                    "mean_latency_ms": report.get("run", {}).get("mean_latency_ms"),
                    "p95_latency_ms": report.get("run", {}).get("p95_latency_ms"),
                    "provider_errors": report.get("run", {}).get("provider_errors"),
                    "truncations": report.get("run", {}).get("completion_truncations"),
                    "blockers": report.get("release_report", {}).get("blocker_failures"),
                }
            )
        st.write("**Current repeated critical-timeout trials**")
        st.dataframe(pd.DataFrame(trial_rows), use_container_width=True, hide_index=True)

    stability = data.get("repeated_qualification", {}).get("stability", {})
    if stability:
        s1, s2, s3 = st.columns(3)
        s1.metric("Healthy-route stable", "YES" if stability.get("stable") else "NO")
        s2.metric("Production SHIP rate", f"{stability.get('production_ship_rate', 0) * 100:.0f}%")
        s3.metric("Behavioral SHIP rate", f"{stability.get('behavioral_ship_rate', 0) * 100:.0f}%")

st.subheader("Interpretation")
st.write(
    "The frozen Phase 1.8 SHIP is a historical release qualification for its measured observation window. "
    "Later operational runs are intentionally allowed to expose regressions and feed the longer-window maturity gate. "
    "Unfavorable new evidence is not discarded or used to retroactively rewrite the earlier measured result."
)
st.caption("Cost evidence is an optimization signal only and never overrides safety, completeness, or latency gates.")
