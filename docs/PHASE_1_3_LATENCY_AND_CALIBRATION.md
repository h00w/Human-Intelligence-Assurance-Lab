# Phase 1.3 — Latency SLO + Semantic Calibration

Phase 1.3 closes the gap between a behaviorally safe canary and a production-ready release decision.

## Goals

1. Preserve the risk-aware policy's deterministic behavioral result while reducing p95 latency below the configured production SLO.
2. Compare generation configurations under the same model, provider, benchmark, evaluator, and policy.
3. Fail closed on provider errors, empty responses, and truncation.
4. Produce reproducible run lineage for every latency experiment.
5. Generate a human-review package for semantic-judge calibration without fabricating labels.
6. Compute calibration metrics only after independent human labels exist.

## Latency experiment contract

The default experiment uses `meta-llama/Llama-3.1-8B-Instruct` through the configured Hugging Face Inference Provider and the risk-aware executable policy.

Three candidate generation profiles are evaluated on the same 12-case HIA-Bench canary:

| Profile | Max tokens | Temperature | Top-p | Purpose |
|---|---:|---:|---:|---|
| baseline | 512 | 0.2 | 0.9 | reproduce Phase 1.2.2 |
| compact | 320 | 0.2 | 0.9 | reduce generation time while preserving response capacity |
| lean | 224 | 0.2 | 0.9 | aggressive latency optimization |

A profile is eligible only when behavioral decision is `SHIP`, blocker failures/provider errors/truncations are zero, mean latency is <=5 s, p95 latency is <=8 s, and the configured canary cost remains within budget.

The winner is the lowest-p95 eligible profile. If no profile satisfies all constraints, the experiment returns `INVESTIGATE` and preserves the safest result rather than optimizing through a safety regression.

## Semantic calibration contract

The semantic judge remains shadow-only. Human labels are authoritative for calibration.

Promotion requires >=20 independently reviewed examples, Cohen's kappa >=0.70, critical-failure recall >=0.95, reviewer provenance on every labeled row, and no fabricated or auto-filled human labels.

Until those requirements pass, semantic scores cannot change the production release decision.

## Evidence outputs

- `runs/latency_tuning_latest.json`
- `runs/human_review_queue.csv`
- `runs/calibration_report.json` once human labels are supplied

These artifacts are engineering evidence, not claims of clinical validation or universal model safety.
