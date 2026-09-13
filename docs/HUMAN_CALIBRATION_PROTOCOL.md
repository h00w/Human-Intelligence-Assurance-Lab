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

1. Generate the semantic human-review queue using the existing semantic-shadow workflow.
2. Give each reviewer the same frozen response set and rubric, but do not expose the other reviewer's labels.
3. Record `scenario_id`/`sample_id`, `reviewer_id`, `human_pass`, the frozen `judge_pass`, and risk/critical status.
4. Merge reviewer files only after both reviews are complete.
5. For disagreements, obtain an explicit adjudicated label and preserve the original two labels.
6. Run `python scripts/score_human_calibration.py` against the merged CSV.
7. Publish `runs/calibration_report.json` only from explicit human labels. Never synthesize missing judgments.

The scorer accepts either `reviewer_id` or the legacy `reviewer` column. A single reviewer cannot unlock release-critical semantic judging.

## Current status

**BLOCKED ON HUMAN WORK.** Engineering support is complete, but no independent labels are invented or inferred by HIA-Lab. Until the thresholds above are satisfied, semantic judging remains shadow-only and Phase 1 v1.0 readiness remains blocked.
