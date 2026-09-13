from __future__ import annotations

import pandas as pd
import streamlit as st

from hia.runner import run_demo

st.set_page_config(page_title="Human Intelligence Assurance Lab", page_icon="🧭", layout="wide")
st.title("Human Intelligence Assurance Lab")
st.caption("HIA-Bench v0.1 · Emotional Intelligence Assurance & Release Gate")

scenarios, results, report = run_demo()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Release decision", report.decision)
c2.metric("Pass rate", f"{report.pass_rate:.1%}")
c3.metric("Critical failures", report.critical_failures)
c4.metric("Privacy violations", report.privacy_violations)

st.subheader("Release gate")
if report.decision == "SHIP":
    st.success("SHIP — all hard gates and minimum quality thresholds passed.")
elif report.decision == "INVESTIGATE":
    st.warning("INVESTIGATE — no hard blocker, but quality/regression thresholds are not met.")
else:
    st.error("HOLD — at least one hard safety or privacy gate failed.")

st.write("\n".join(f"- {reason}" for reason in report.reasons))

st.subheader("Domain pass rates")
domain_df = pd.DataFrame(
    [{"domain": k, "pass_rate": v} for k, v in report.domain_pass_rates.items()]
).set_index("domain")
st.bar_chart(domain_df)

st.subheader("HIA-Bench scenario explorer")
rows = []
by_result = {r.scenario_id: r for r in results}
for s in scenarios:
    r = by_result[s.id]
    rows.append(
        {
            "id": s.id,
            "domain": s.domain,
            "risk": s.risk_level,
            "severity": s.release_severity,
            "passed": r.passed,
            "violations": ", ".join(r.violations),
            "prompt": s.input.user_message,
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.info(
    "Phase 1 uses synthetic text scenarios and auditable deterministic checks. "
    "It does not diagnose users, infer ground-truth emotions, or claim clinical validation."
)
