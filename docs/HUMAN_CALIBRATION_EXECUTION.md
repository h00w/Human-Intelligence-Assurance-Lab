# Human Calibration Execution Package

This runbook turns the existing semantic-shadow queue into an auditable independent-human calibration workflow. It does **not** generate, infer, backfill, or repair human labels.

## Frozen evidence boundary

The source batch is `runs/human_review_queue.csv` in the public HIA-Lab Hugging Face dataset. The execution package computes a SHA-256 fingerprint over the frozen scenario identity, domain, risk, candidate response, and judge evidence. Reviewer imports are accepted only when all frozen reviewer-visible fields match the source batch exactly.

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

The reviewer CSVs deliberately exclude `judge_pass` and `judge_overall`. This avoids anchoring reviewers on the model judge.

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

If reviewers agree on every sample, `merged_human_labels.csv` is immediately ready for scoring.

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

## 5. Score calibration

```bash
HIA_HUMAN_REVIEW_CSV=artifacts/human_calibration_import/merged_human_labels.csv \
python scripts/score_human_calibration.py
```

The scorer fails closed on incomplete rows or duplicate reviewer/sample labels. It publishes `runs/calibration_report.json` only from explicit reviewer evidence. A non-passing calibration report exits non-zero and semantic judging remains shadow-only.

## 6. Public dashboard

`pages/7_Human_Calibration.py` displays:

- frozen batch size and fingerprint;
- blinded reviewer downloads;
- package readiness state;
- reviewer/resolution counts;
- inter-reviewer kappa;
- judge-vs-human kappa;
- critical-failure recall;
- release-critical semantic status and blocking reasons.

## Evidence-integrity rule

No software path in this package is permitted to manufacture a human label. Automation may package, hash, validate, merge, adjudication-check, score, publish, and visualize labels, but the judgments themselves must come from independent human reviewers.
