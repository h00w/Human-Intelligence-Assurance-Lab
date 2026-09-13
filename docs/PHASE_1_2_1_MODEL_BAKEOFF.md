# Phase 1.2.1 — Live Model Bakeoff

Phase 1.2.1 turns HIA-Lab from a single-candidate release check into a safety-first model-selection system.

## Why this increment exists

The Granite baseline completed all 12 provider calls but produced 7 token-budget truncations. HIA-Lab correctly treated those completions as incomplete evidence and returned HOLD. The next engineering question is therefore not “how do we relax the gate?” but “does a different model satisfy the same contract more reliably?”

## Default bakeoff

- Baseline: `ibm-granite/granite-4.2-3b`
- Candidate: `meta-llama/Llama-3.1-8B-Instruct`
- Provider: Hugging Face Inference Providers / DeepInfra
- Test set: same 12-case HIA-Bench canary

Granite keeps its current reasoning-oriented generation budget (`max_tokens=1024`, temperature 1.0, top_p 0.95). Llama uses a shorter instruction-response configuration (`max_tokens=512`, temperature 0.2, top_p 0.9).

## Selection contract

The bakeoff uses the same lexicographic policy as `hia.comparison`:

1. fewer blocker failures
2. stronger release decision
3. materially higher deterministic pass rate
4. calibrated semantic score, when calibration is valid
5. lower latency after safety/quality parity
6. lower cost after safety/quality parity

Phase 1.2.1 explicitly sets `semantic_score_used=false`; semantic evidence remains shadow-only until the human calibration contract is satisfied.

## Evidence

Each bakeoff publishes `runs/model_bakeoff_latest.json` to:

- Hugging Face Dataset
- Hugging Face Storage Bucket
- GitHub Actions artifact
- public HIA-Lab dashboard

The report includes both complete candidate evaluation reports, their lineage fingerprints, operational evidence, and the comparison result.

## Interpretation boundary

A winner means “preferred under this HIA-Bench canary and these exact model/provider/generation configurations.” It does not establish general model superiority, clinical validation, or universal emotional-intelligence quality.
