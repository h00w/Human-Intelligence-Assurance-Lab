# Human Calibration Execution Package

This runbook turns qualified Phase 1 candidate evidence into an auditable independent-human calibration workflow. It does **not** generate, infer, backfill, or repair human labels.

## Frozen evidence boundary

The reviewer batch is `runs/human_review_queue.csv` in the public HIA-Lab Hugging Face dataset. If that file does not yet exist, `scripts/prepare_human_calibration_package.py` freezes the candidate responses from the current **SHIP** `runs/adaptive_hedging_latest.json` evidence and publishes that exact batch. It refuses to freeze a non-SHIP adaptive run.

The SHA-256 batch fingerprint covers only immutable reviewer-visible evidence: scenario identity, domain, risk level, and candidate response. Semantic-judge output is deliberately **not** part of the frozen human-review batch. Judge scoring happens only after independent human review, eliminating judge-output anchoring.

The package requires at least 20 samples and preserves the Phase 1 thresholds:

- at least 20 resolved samples;
- at least 2 independent reviewers per sample;
- inter-reviewer Cohen's kappa >= 0.70;
- judge-vs-human Cohen's kappa >= 0.70;
- critical human-failure recall >= 0.95.

## 1. Generate blinded reviewer files

```bash
python scripts/prepare_human_calibration_package.py
```

Outputs under `artifacts/human_calibration_package/`:

- `reviewer_A.csv`
- `reviewer_B.csv`
- `REVIEWER_INSTRUCTIONS.md`
- `manifest.json`

The manifest records the frozen-batch SHA-256, source adaptive evidence, qualification epoch/policy when available, and `judge_status=PENDING_POST_REVIEW_SHADOW_JUDGE`.

The same reviewer files are available through the public **Human Calibration** Streamlit page.

## 2. Independent review

Each reviewer completes every `human_pass` cell with `true` or `false` and may add rationale under `notes`.

Rules:

- do not change reviewer ID;
- do not edit frozen sample fields;
- do not add/delete/reorder samples;
- do not consult the other reviewer's labels before both sheets are complete;
- do not use an LLM to supply the human judgment.

## 3. Validate and import

```bash
python scripts/import_human_calibration_reviews.py reviewer_A.csv reviewer_B.csv
```

Validation rejects:

- missing or invalid labels;
- duplicate or reused reviewer identities;
- unknown/missing/duplicate samples;
- candidate-response edits;
- domain/risk/scenario mutations;
- incomplete frozen-batch coverage.

For a pre-judge frozen batch, a clean import reports `READY_FOR_POST_REVIEW_JUDGE` rather than pretending calibration can already be scored.

## 4. Explicit adjudication

If there are disagreements, import exits non-zero and creates `adjudication_queue.csv`. A human adjudicator fills:

- `adjudicator_id`
- `adjudicated_pass`
- optional `adjudication_notes`

Then rerun:

```bash
python scripts/import_human_calibration_reviews.py \
  reviewer_A.csv reviewer_B.csv \
  --adjudication adjudication_queue.csv
```

The importer requires exactly one adjudication for every disagreement and rejects adjudications for samples that did not disagree. Original reviewer labels remain preserved.

## 5. Run the semantic judge only after human review

After both independent reviewer files are complete and any disagreements are adjudicated:

```bash
HF_TOKEN=... \
HIA_JUDGE_MODEL=<independent-model> \
HIA_JUDGE_PROVIDER=<provider-or-auto> \
python scripts/run_post_review_semantic_judge.py
```

This script:

- verifies that reviewed sample IDs exactly match the frozen queue;
- reuses the frozen candidate responses without regenerating them;
- runs the semantic judge once per frozen sample;
- writes `artifacts/human_calibration_judge/post_review_semantic_judge.json`;
- writes `artifacts/human_calibration_judge/calibration_scoring_input.csv` with judge labels attached to the preserved human labels;
- remains shadow-only and does not itself make a release decision.

No judge inference is required merely to prepare or distribute reviewer files.

## 6. Score calibration

```bash
HIA_HUMAN_REVIEW_CSV=artifacts/human_calibration_judge/calibration_scoring_input.csv \
python scripts/score_human_calibration.py
```

The scorer fails closed on incomplete rows or duplicate reviewer/sample labels. It publishes `runs/calibration_report.json` only from explicit reviewer evidence plus post-review judge labels. A non-passing calibration report exits non-zero and semantic judging remains shadow-only.

## 7. Public dashboard

`pages/7_Human_Calibration.py` displays:

- frozen batch size and fingerprint;
- source qualification provenance;
- blinded reviewer downloads;
- package readiness and post-review-judge state;
- reviewer/resolution counts;
- inter-reviewer kappa;
- judge-vs-human kappa;
- critical-failure recall;
- release-critical semantic status and blocking reasons.

## Evidence-integrity rule

No software path in this package is permitted to manufacture a human label. Automation may freeze qualified candidate evidence, package, hash, validate, merge, adjudication-check, post-review judge, score, publish, and visualize labels, but the human judgments themselves must come from independent reviewers. The semantic judge is intentionally delayed until those human judgments are frozen.
