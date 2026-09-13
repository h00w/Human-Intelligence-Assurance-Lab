# Human Intelligence Assurance Lab

**Production architecture for measurable, safe, emotionally aware, human-centered AI.**

[![CI](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml)
[![Phase 1.5 Provider Resilience](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/provider-resilience.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/provider-resilience.yml)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/h0000w/Human-Intelligence-Assurance-Lab)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-yellow)](https://huggingface.co/spaces/h0000w/Human-Intelligence-Assurance-Lab)

> **Independent research and engineering portfolio project.** This repository is inspired by publicly described human-centered AI product directions. It does not use proprietary BalanX-Bio data, source code, models, confidential information, or internal architecture.

## What HIA-Lab proves

Emotionally aware and longitudinal AI should not be released because it merely *sounds* empathetic. HIA-Lab converts human-centered AI requirements into executable benchmark contracts, deterministic safety gates, real-model evidence, controlled model/policy/provider experiments, operational SLOs, repeated-run qualification, semantic-calibration workflows, and reproducible release lineage.

The project deliberately allows later evidence to overturn earlier positive results. A fast or high-scoring configuration can never compensate for a safety blocker, incomplete response, or missing evidence.

## Current production evidence — Phase 1.5

Phase 1.4 showed that the previous single-route DeepInfra configuration did **not** reproduce reliably: production SHIP recurrence was 0%, median trial p95 was 20.14 s, worst p95 was 41.23 s, and one critical wellness response truncated. The correct executive result was **HOLD**.

Phase 1.5 remediated those measured failure modes through a controlled provider-route bakeoff, bounded critical-response policy, hard inference deadlines, and an ordered fallback route. The release thresholds were **not relaxed**.

### Provider-route bakeoff

Same model, risk-aware policy, 12-case canary, evaluator, token budget, temperature, and top-p across all routes:

| Provider | Behavioral | Pass rate | Blockers | Errors | Truncations | Mean latency | p95 latency |
|---|---|---:|---:|---:|---:|---:|---:|
| **Nscale** | **SHIP** | **100%** | **0** | **0** | **0** | **1.23 s** | **2.26 s** |
| Novita | SHIP | 100% | 0 | 0 | 0 | 1.65 s | 6.25 s |
| DeepInfra | SHIP | 100% | 0 | 0 | 0 | 3.86 s | 7.99 s |

**Selected primary route: Nscale.** All three routes were eligible in this run, but Nscale had the lowest eligible p95 latency.

### Deadline-aware route

```text
Nscale primary
   │ hard request deadline: 4 s
   ▼
complete response? ── yes ──> evaluate
   │
   no / timeout / truncation
   ▼
Novita fallback
   │ hard request deadline: 4 s
   ▼
evaluate complete evidence
```

End-to-end latency includes every attempted route. Failover cannot erase time already spent on the primary route.

### Five-trial production requalification

Five independent 12-case trials were run after provider selection: **60 real model generations**.

| Qualification metric | Result |
|---|---:|
| Behavioral SHIP rate | **100%** |
| Production SHIP rate | **100%** |
| Blocker-trial rate | **0%** |
| Provider-error trial rate | **0%** |
| Truncation-trial rate | **0%** |
| Mean latency | **1.21 s** |
| Mean latency 95% CI | **1.16–1.25 s** |
| Median trial p95 | **2.11 s** |
| Trial-p95 95% CI | **1.92–2.47 s** |
| Worst observed trial p95 | **2.70 s** |
| Production SLO | **≤8 s p95** |
| Executive decision | **SHIP** |

Every repeated trial passed the unchanged Phase 1.4 production-confidence contract.

**Important limitation:** the live qualification did not need to invoke fallback. Nscale completed all 60 qualification requests before the 4-second primary deadline. The fallback mechanism is unit-tested for timeout and truncation recovery, but live fault-injection evidence is a separate next milestone.

## Phase history

### Phase 1 — HIA-Bench v0.1

- **100 synthetic scenarios** across everyday affect, interpersonal conflict, vulnerability, dependency, epistemic risk, and wellness.
- deterministic safety/privacy checks with lexicographic **SHIP / INVESTIGATE / HOLD** decisions;
- blocker failures cannot be averaged away;
- empty responses and incomplete evidence fail closed.

### Phase 1.1 — Real-model evidence

The live canary evaluates **12 higher-risk cases (two per domain)** through Hugging Face Inference Providers and records raw responses, provider/model identity, latency, token usage, cost evidence, truncation, deterministic violations, domain pass rates, and run lineage.

### Phase 1.2 — Model, policy, and semantic assurance

- live model bakeoff;
- executable policy ablation;
- composite behavioral + operational production gate;
- semantic judge kept **shadow-only** pending independent human calibration.

The semantic calibration contract requires at least 20 genuinely human-reviewed samples, Cohen's kappa >=0.70, critical-failure recall >=0.95, and reviewer provenance. HIA-Lab does not fabricate human annotations.

### Phase 1.3 — Single-run SLO closure

The risk-aware Llama configuration reached a favorable single-run production SHIP with 100% behavioral pass, 0 blockers/errors/truncations, and p95 latency 6.50 s. Phase 1.4 subsequently demonstrated why a single favorable run was insufficient evidence.

### Phase 1.4 — Repeated-run production confidence

Five fixed DeepInfra trials exposed substantial tail-latency variance and a stochastic truncation:

- production SHIP rate: **0%**;
- behavioral SHIP rate: 80%;
- median trial p95: 20.14 s;
- worst trial p95: 41.23 s;
- blocker/truncation trial rate: 20%;
- executive decision: **HOLD**.

This was the evidence that motivated Phase 1.5 rather than weakening the SLO.

### Phase 1.5 — Provider resilience & critical-response control

- controlled Nscale / Novita / DeepInfra route bakeoff;
- bounded critical answers with mandatory safety content front-loaded and a <=120-word target;
- critical wellness guard against speculative diagnostic lists;
- hard provider deadlines;
- timeout/error/truncation fallback;
- repeated requalification under the unchanged Phase 1.4 contract;
- measured executive result: **SHIP**.

## Production gate

```text
behavioral HOLD
    -> HOLD

provider error / empty response / truncation
    -> HOLD

behavioral INVESTIGATE
    -> INVESTIGATE

behavioral SHIP + operational regression
    -> INVESTIGATE

single production SHIP
    -> requires repeated qualification

repeated behavioral + operational PASS
    -> PRODUCTION SHIP

semantic judge
    -> shadow-only until human calibration passes
```

## Architecture

```text
HIA-Bench
   │
   ├── candidate model + executable policy
   │          ├── bounded critical-response control
   │          └── raw response + lineage
   │
   ├── provider-route qualification
   │          ├── primary route + hard deadline
   │          └── fallback route + attempt provenance
   │
   ├── deterministic safety gate
   ├── completeness gate
   ├── operational SLO gate
   ├── repeated-run stability gate
   └── semantic judge (shadow)
                  │
                  ▼
           Executive Assurance
                  │
          HOLD / INVESTIGATE / SHIP
                  │
      Dataset + Bucket + Space + Actions
```

## Evidence and publication

- GitHub: `h00w/Human-Intelligence-Assurance-Lab`
- Dataset: `h0000w/Human-Intelligence-Assurance-Lab`
- Evaluator/research artifact: `h0000w/Human-Intelligence-Assurance-Lab`
- Space: `h0000w/Human-Intelligence-Assurance-Lab`
- Storage Bucket: `h0000w/Human-Intelligence-Assurance-Lab-storage`

Key published evidence:

```text
runs/
├── live_eval_latest.json
├── model_bakeoff_latest.json
├── policy_ablation_latest.json
├── latency_tuning_latest.json
├── stability_study_latest.json
├── provider_resilience_latest.json
├── semantic_shadow_latest.json
├── human_review_queue.csv
├── calibration_report.json
└── executive_assurance_manifest.json
```

The Space uses **Docker + CPU Basic**. Model inference is remote through Hugging Face Inference Providers.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
pytest -q
python -m hia.runner
streamlit run app.py
```

Real-model experiments require `HF_TOKEN`.

## Documentation

- [`docs/PHASE_1_SPEC.md`](docs/PHASE_1_SPEC.md)
- [`docs/PHASE_1_1_REAL_MODEL_EVAL.md`](docs/PHASE_1_1_REAL_MODEL_EVAL.md)
- [`docs/PHASE_1_2_SEMANTIC_CALIBRATION.md`](docs/PHASE_1_2_SEMANTIC_CALIBRATION.md)
- [`docs/PHASE_1_2_1_MODEL_BAKEOFF.md`](docs/PHASE_1_2_1_MODEL_BAKEOFF.md)
- [`docs/PHASE_1_2_2_POLICY_ABLATION.md`](docs/PHASE_1_2_2_POLICY_ABLATION.md)
- [`docs/PHASE_1_2_3_COMPOSITE_PRODUCTION_GATE.md`](docs/PHASE_1_2_3_COMPOSITE_PRODUCTION_GATE.md)
- [`docs/PHASE_1_3_LATENCY_AND_CALIBRATION.md`](docs/PHASE_1_3_LATENCY_AND_CALIBRATION.md)
- [`docs/PHASE_1_4_PRODUCTION_CONFIDENCE.md`](docs/PHASE_1_4_PRODUCTION_CONFIDENCE.md)
- [`docs/PHASE_1_4_RESULT.md`](docs/PHASE_1_4_RESULT.md)
- [`docs/PHASE_1_5_PROVIDER_RESILIENCE.md`](docs/PHASE_1_5_PROVIDER_RESILIENCE.md)
- [`evals/scenarios/hia_bench_v0_1.jsonl`](evals/scenarios/hia_bench_v0_1.jsonl)

## Next qualification milestone

**Phase 1.6 — Fault Injection & Infrastructure Qualification:** deliberately exercise primary-route timeout/truncation/failure, prove live fallback behavior, compare routed providers with dedicated inference infrastructure, and expand the repeated qualification window before treating resilience as production-grade infrastructure evidence.

After the resilience layer is validated under injected faults, Phase 2 moves into governed longitudinal memory and relationship-safety evaluation.

## Scientific and safety boundaries

HIA-Bench is a synthetic engineering benchmark. It does **not** diagnose medical or mental-health conditions, establish ground-truth user emotion, clinically validate a product, claim consciousness/AGI, or replace independent human review for high-risk deployments. Results are scoped to the tested benchmark, model, policy, provider routes, generation configuration, and observation window.

## License

MIT. Benchmark scenarios are synthetic and provided for research, evaluation, and engineering use.
