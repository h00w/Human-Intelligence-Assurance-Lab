# Independent Human Semantic Calibration Protocol

Phase 1 does not allow a model judge to certify itself. The semantic judge remains **shadow-only** until this protocol passes.

## Release requirements

- at least **20 resolved samples**;
- at least **2 independent human reviewers per sample**;
- reviewer identity/provenance recorded for every label;
- disagreements require explicit adjudication rather than silent majority fabrication;
- inter-reviewer Cohen's kappa **>= 0.70**;
- judge-vs-human Cohen's kappa **>= 0.70**;
- critical human-failure recall **>= 0.95**.

## Reviewer workflow

1. Freeze at least 20 candidate responses from current qualified **SHIP** adaptive evidence. The package refuses to create a batch from a non-SHIP adaptive run.
2. Record a SHA-256 over the reviewer-visible frozen evidence: scenario ID, domain, risk level, and candidate response.
3. Generate reviewer files with `python scripts/prepare_human_calibration_package.py` or download them from the Human Calibration dashboard.
4. Give Reviewer A and Reviewer B the same frozen response set and rubric. Reviewer sheets contain **no semantic-judge labels or scores**, and neither reviewer may see the other's labels before completion.
5. Each reviewer records `human_pass` and optional notes for every sample. Reviewer identity/provenance is fixed in the sheet.
6. Import both completed sheets with `python scripts/import_human_calibration_reviews.py reviewer_A.csv reviewer_B.csv`.
7. The importer verifies exact frozen-batch coverage and rejects missing labels, modified candidate responses, unknown samples, duplicate sample rows, and reused reviewer identities.
8. For disagreements, complete the generated `adjudication_queue.csv` with an explicit human `adjudicator_id` and `adjudicated_pass`, then rerun the importer with `--adjudication`.
9. **Only after human review is complete**, run `scripts/run_post_review_semantic_judge.py` on those same frozen candidate responses. This removes judge-output anchoring by construction.
10. Run `scripts/score_human_calibration.py` against the resulting `calibration_scoring_input.csv`.
11. Publish `runs/calibration_report.json` only from explicit human labels plus the post-review shadow judge. Never synthesize, infer, or silently skip missing judgments.

The scorer accepts either `reviewer_id` or the legacy `reviewer` column, but incomplete rows fail closed rather than being omitted from calibration. A single reviewer cannot unlock release-critical semantic judging.

See `docs/HUMAN_CALIBRATION_EXECUTION.md` for the complete operational runbook.

## Current status

**ENGINEERING READY / BLOCKED ON GENUINE HUMAN LABELS.** Frozen qualified-response packaging, blinded Reviewer A/B sheets, import validation, explicit adjudication, post-review semantic-judge tooling, strict scoring, and the public dashboard are implemented. No independent human labels are invented or inferred by HIA-Lab. Until genuine reviewers complete the batch and all thresholds above are satisfied, semantic judging remains shadow-only and Phase 1 v1.0 readiness remains blocked.
