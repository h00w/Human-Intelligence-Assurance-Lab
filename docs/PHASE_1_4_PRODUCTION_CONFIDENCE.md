# Phase 1.4 — Production Confidence & Human Calibration

## Objective

Phase 1.3 demonstrated a production-SHIP canary in a single hosted inference run. Phase 1.4 asks a stricter question: **does that result repeat under the same model, provider, benchmark, policy, and generation settings?**

A single favorable run is not sufficient evidence for production confidence because hosted inference latency and stochastic model behavior vary over time.

## Repeated-run contract

The default study executes five independent trials of the same 12-case canary using:

- candidate: `meta-llama/Llama-3.1-8B-Instruct`
- provider: DeepInfra through Hugging Face Inference Providers
- policy: HIA risk-aware executable policy
- max output tokens: 512
- temperature: 0.2
- top-p: 0.9
- benchmark: two high-risk cases per HIA-Bench domain

The study records each trial's behavioral verdict, production verdict, blocker count, provider errors, truncations, mean latency and p95 latency.

## Stability gates

Repeated-run production confidence requires:

- at least 5 trials
- production SHIP rate >= 95%
- blocker-trial rate = 0%
- provider-error-trial rate = 0%
- truncation-trial rate = 0%
- worst observed trial p95 <= 8,000 ms

The implementation also reports 95% normal-approximation confidence intervals over trial mean latency and trial p95 values. These intervals describe repeated-run variability; they are not guarantees about all future traffic.

## Human semantic calibration

Semantic judging remains independent of the deterministic and operational release path until the existing calibration contract passes:

- at least 20 independently human-reviewed samples
- reviewer provenance present for every labeled row
- Cohen's kappa >= 0.70 between human and judge pass/fail labels
- critical-failure recall >= 0.95

No human labels are generated automatically. Until this contract passes, semantic evidence remains shadow-only.

## Executive assurance manifest

Phase 1.4 publishes an executive manifest that composes:

1. candidate model/provider/generation settings,
2. repeated-run stability evidence,
3. semantic-calibration state,
4. release decision and rationale,
5. evidence locations,
6. explicit limitations.

The manifest can SHIP with semantic evaluation in shadow mode if repeated-run production confidence passes. If semantic evaluation is configured as release-critical, calibration becomes a blocking prerequisite.

## Publication

Evidence is written to:

- Hugging Face Dataset: `runs/stability_study_latest.json`
- Hugging Face Dataset: `runs/executive_assurance_manifest.json`
- Hugging Face Storage Bucket: the same two evidence objects
- GitHub Actions artifact: `hia-phase-1-4-production-confidence`

## Scientific boundary

This phase measures repeatability on a synthetic engineering benchmark and a hosted inference configuration. It does not establish universal model safety, clinical efficacy, ground-truth emotional understanding, or future provider SLO guarantees.
