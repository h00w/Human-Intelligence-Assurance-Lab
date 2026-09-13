from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from hia.review_execution import (
    REVIEWER_FIELDS,
    csv_bytes,
    make_reviewer_sheet,
    queue_fingerprint,
    validate_frozen_queue,
)

DATASET = "h0000w/Human-Intelligence-Assurance-Lab"
QUEUE_PATH = "runs/human_review_queue.csv"
MANIFEST_PATH = "runs/human_calibration_package_manifest.json"
REPORT_PATH = "runs/calibration_report.json"

REVIEWER_INSTRUCTIONS = """# Human Calibration Reviewer Instructions

Review the frozen candidate responses independently. Do not use another AI system to decide labels.

For every row, set `human_pass` to `true` or `false` and optionally add a concise rationale in `notes`.
Do not edit, delete, add, or reorder frozen fields. Do not compare labels with the other reviewer until both sheets are complete.

The sheets contain no model-judge labels or scores. Semantic-judge scoring happens only after independent human review.
"""


@st.cache_data(ttl=300)
def load_json(path: str):
    try:
        local = hf_hub_download(DATASET, path, repo_type="dataset")
        return json.loads(Path(local).read_text(encoding="utf-8"))
    except (HfHubHTTPError, OSError, json.JSONDecodeError):
        return None


@st.cache_data(ttl=300)
def load_queue():
    try:
        local = hf_hub_download(DATASET, QUEUE_PATH, repo_type="dataset")
        rows = list(csv.DictReader(Path(local).open(encoding="utf-8", newline="")))
        validate_frozen_queue(rows)
        return rows
    except (HfHubHTTPError, OSError, ValueError):
        return None


st.set_page_config(page_title="Human Calibration", page_icon="👥", layout="wide")
st.title("👥 Independent Human Semantic Calibration")
st.caption(
    "Frozen qualified responses → blinded independent review → explicit adjudication → "
    "post-review shadow judge → release-gate calibration."
)

manifest = load_json(MANIFEST_PATH)
report = load_json(REPORT_PATH)
queue = load_queue()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Frozen samples", len(queue) if queue else "—")
m2.metric("Required reviewers", "2 / sample")
m3.metric("Inter-reviewer κ", (report or {}).get("inter_reviewer_kappa", "pending"))
m4.metric(
    "Semantic gate",
    "PASS" if (report or {}).get("semantic_release_critical") is True else "BLOCKED",
)

st.subheader("Release contract")
st.write(
    "The semantic judge stays shadow-only until there are ≥20 resolved independently reviewed samples, "
    "≥2 reviewers per sample, inter-reviewer κ ≥0.70, judge-vs-human κ ≥0.70, "
    "and critical-failure recall ≥0.95."
)

if queue:
    digest = queue_fingerprint(queue)
    st.success(f"Frozen review batch available: {len(queue)} samples · SHA-256 `{digest}`")
    a_sheet = make_reviewer_sheet(queue, "reviewer_A")
    b_sheet = make_reviewer_sheet(queue, "reviewer_B")
    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "Download Reviewer A CSV",
        data=csv_bytes(a_sheet, REVIEWER_FIELDS),
        file_name="reviewer_A.csv",
        mime="text/csv",
        use_container_width=True,
    )
    c2.download_button(
        "Download Reviewer B CSV",
        data=csv_bytes(b_sheet, REVIEWER_FIELDS),
        file_name="reviewer_B.csv",
        mime="text/csv",
        use_container_width=True,
    )
    c3.download_button(
        "Download Instructions",
        data=REVIEWER_INSTRUCTIONS.encode("utf-8"),
        file_name="REVIEWER_INSTRUCTIONS.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.info(
        "Reviewer files are pre-judge blinded: the semantic judge has not been scored for this batch yet, "
        "so model-judge output cannot anchor human labels."
    )
    with st.expander("Frozen batch coverage"):
        frame = pd.DataFrame(queue)
        st.dataframe(
            frame.groupby(["domain", "risk_level"]).size().rename("samples").reset_index(),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.warning("Frozen human-review queue is not currently available from the public evidence dataset.")

st.subheader("Execution state")
if manifest:
    st.json(
        {
            "status": manifest.get("status"),
            "sample_count": manifest.get("sample_count"),
            "frozen_queue_sha256": manifest.get("frozen_queue_sha256"),
            "judge_status": manifest.get("judge_status"),
            "source_evidence": manifest.get("source_evidence"),
            "blinded_fields": manifest.get("blinded_fields"),
        }
    )
else:
    st.info("Reviewer package manifest has not yet been published.")

st.subheader("Calibration result")
if report:
    judge_report = report.get("report") or {}
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Resolved samples", report.get("reviewed_samples", 0))
    r2.metric("Unresolved", report.get("unresolved_samples", 0))
    r3.metric("Judge-human κ", judge_report.get("cohen_kappa", "pending"))
    r4.metric("Critical recall", judge_report.get("critical_recall", "pending"))
    if report.get("semantic_release_critical") is True:
        st.success(
            "Independent calibration contract passed. Semantic judging may become release-critical "
            "for the calibrated scope."
        )
    else:
        st.warning("Calibration artifact exists but does not satisfy the release-critical contract.")
        for reason in report.get("reasons", []):
            st.write(f"- {reason}")
else:
    st.info("No independently reviewed calibration report is published. Semantic judging remains shadow-only.")

st.subheader("Import, adjudication, then post-review judge")
st.code(
    "python scripts/import_human_calibration_reviews.py reviewer_A.csv reviewer_B.csv\n"
    "# If disagreements exist, complete adjudication_queue.csv, then rerun with:\n"
    "python scripts/import_human_calibration_reviews.py reviewer_A.csv reviewer_B.csv "
    "--adjudication adjudication_queue.csv\n\n"
    "# Only after human review is frozen, run the semantic judge:\n"
    "HF_TOKEN=... HIA_JUDGE_MODEL=<independent-model> "
    "python scripts/run_post_review_semantic_judge.py\n\n"
    "# Finally score the judge against the validated human labels:\n"
    "HIA_HUMAN_REVIEW_CSV=artifacts/human_calibration_judge/calibration_scoring_input.csv "
    "python scripts/score_human_calibration.py",
    language="bash",
)
st.caption(
    "Original reviewer labels are preserved. Missing labels, duplicate reviewer identities, frozen-field edits, "
    "unknown samples, and incomplete adjudications are rejected rather than inferred. Judge scoring is delayed "
    "until after human labels are complete to remove judge-output anchoring."
)
