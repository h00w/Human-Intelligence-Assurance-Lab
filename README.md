# Human Intelligence Assurance Lab

**Production architecture for measurable, safe, emotionally aware, human-centered AI.**

[![CI](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml)
[![Phase 1.7 Hedged Requests](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/hedged-requests.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/hedged-requests.yml)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/h0000w/Human-Intelligence-Assurance-Lab)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-yellow)](https://huggingface.co/spaces/h0000w/Human-Intelligence-Assurance-Lab)

> **Independent research and engineering portfolio project.** This repository is inspired by publicly described human-centered AI product directions. It does not use proprietary BalanX-Bio data, source code, models, confidential information, or internal architecture.

## What HIA-Lab proves

Emotionally aware and longitudinal AI should not be released because it merely *sounds* empathetic. HIA-Lab converts human-centered requirements into executable benchmark contracts, deterministic safety gates, real-model evidence, controlled model/policy/provider experiments, operational SLOs, repeated-run qualification, fault injection, semantic-calibration workflows, and reproducible release lineage.

The project deliberately allows later evidence to overturn earlier positive results. A fast or high-scoring configuration can never compensate for a blocker, incomplete response, missing evidence, or failed production SLO.

## Current production evidence — Phase 1.7

Phase 1.6 proved that the Phase 1.5 sequential fallback architecture recovered safety and completeness after a forced Nscale timeout, but averaged **5.252 s**, exceeding the unchanged **5.000 s mean-latency SLO**. The Phase 1.6 executive result was therefore **HOLD**.

Phase 1.7 changes the routing architecture rather than weakening the gate: if Nscale has not completed by the selected hedge threshold, Novita starts in parallel and the first complete response wins. The losing attempt is still observed during qualification so provider, completion, token/cost, and post-decision provenance are retained.

### Hedge-threshold bakeoff

Same Llama 3.1 8B model, risk-aware policy, 12-case high-risk canary, Nscale primary, Novita fallback, evaluator, generation budget, and production contract:

| Hedge delay | Behavioral | Production | Mean | p95 | Hedge rate | Fallback wins |
|---:|---|---|---:|---:|---:|---:|
| 0.5 s | SHIP | SHIP | 1.194 s | 1.779 s | 100% | 0% |
| 1.0 s | SHIP | SHIP | 1.240 s | 2.306 s | 66.67% | 0% |
| **1.5 s** | **SHIP** | **SHIP** | **1.137 s** | **1.589 s** | **8.33%** | **0%** |
| 2.0 s | SHIP | SHIP | 1.301 s | 2.781 s | 8.33% | 0% |

**Selected hedge delay: 1.5 s.** It produced the lowest eligible p95 in this run while avoiding the heavy duplicate-work rate seen at shorter delays.

### Forced 4-second primary timeout

Nscale was forced to consume its complete 4-second timeout while Novita launched after 1.5 seconds.

| Metric | Result |
|---|---:|
| Behavioral decision | **SHIP** |
| Production decision | **SHIP** |
| Pass rate | **100%** |
| Blockers | **0** |
| Final provider errors | **0** |
| Unrecovered truncations | **0** |
| Mean decision latency | **2.762 s** |
| p95 decision latency | **3.604 s** |
| Hedge rate | **100%** |
| Fallback winner rate | **100%** |

This directly closes the Phase 1.6 timeout-recovery failure under the same `mean <= 5 s` and `p95 <= 8 s` production SLOs.

### Forced truncation and dual degradation

- forced primary truncation → real Novita fallback: behavioral **SHIP**, production **SHIP**, mean **2.426 s**, p95 **3.352 s**, 100% fallback wins, zero blockers/final errors/unrecovered truncations;
- simultaneous Nscale + Novita degradation: correctly **HOLD**.

Hedging never converts missing evidence into a releaseable response.

### Extended qualification

The selected 1.5-second hedge configuration was then run for **10 trials × 12 high-risk scenarios = 120 real generations**.

| Metric | Result |
|---|---:|
| Production SHIP recurrence | **100%** |
| Behavioral SHIP recurrence | **100%** |
| Blocker-trial rate | **0%** |
| Provider-error trial rate | **0%** |
| Truncation-trial rate | **0%** |
| Mean latency | **1.217 s** |
| Mean-latency 95% CI | **1.169–1.265 s** |
| Median trial p95 | **1.866 s** |
| Trial-p95 95% CI | **1.738–2.250 s** |
| Worst observed trial p95 | **2.837 s** |
| Stability verdict | **PASS** |

**Phase 1.7 executive decision: SHIP.**

### Routed vs dedicated infrastructure

Routed hedged inference is **MEASURED**. Dedicated inference remains **NOT_CONFIGURED** and non-release-critical because no endpoint was explicitly provisioned.

HIA-Lab does not silently create billable infrastructure. Once a dedicated endpoint is explicitly available, it should be evaluated against the same benchmark, model, policy, fault scenarios, evaluator, and SLO contract.

## Phase history

### Phase 1 — HIA-Bench v0.1
- 100 synthetic scenarios across six human-centered AI risk domains.
- Deterministic, auditable safety/privacy checks.
- Lexicographic **SHIP / INVESTIGATE / HOLD** decisions.

### Phase 1.1 — Real-model evidence
- Hugging Face routed inference.
- Raw response, latency, token, cost, provider, truncation, violation, and lineage evidence.
- Empty responses and incomplete generations fail closed.

### Phase 1.2 — Model, policy, and semantic assurance
- Live model bakeoff and policy ablation.
- Composite behavioral + operational production gate.
- Semantic judge remains **shadow-only** pending independent human calibration.

### Phase 1.3 — Single-run SLO closure
- Risk-aware Llama configuration reached a favorable single-run production SHIP.
- Later repeated evidence showed why one favorable run was insufficient.

### Phase 1.4 — Repeated-run production confidence
- 5 trials / 60 generations.
- Production SHIP recurrence 0%.
- Median p95 20.14 s; worst p95 41.23 s.
- One critical wellness response truncated.
- Executive decision: **HOLD**.

### Phase 1.5 — Provider resilience & critical-response control
- Nscale / Novita / DeepInfra bakeoff.
- Bounded critical answers and hard request deadlines.
- Nscale selected primary; Novita fallback.
- 5 trials / 60 generations: 100% production SHIP, zero blockers/errors/truncations, worst p95 2.70 s.
- Executive decision: **SHIP**.

### Phase 1.6 — Fault Injection & Infrastructure Qualification
- Forced primary timeout and truncation with real fallback.
- Simultaneous provider degradation test.
- 10-trial / 120-generation healthy-route qualification.
- Sequential timeout recovery: behavioral SHIP but mean 5.252 s > 5.000 s SLO.
- Executive decision: **HOLD**.

### Phase 1.7 — Hedged Requests & Dedicated Infrastructure Bakeoff
- Controlled 0.5 / 1.0 / 1.5 / 2.0 s hedge-threshold bakeoff.
- 1.5 s selected in the measured run.
- Forced 4-second timeout recovery: 2.762 s mean / 3.604 s p95, production **SHIP**.
- Forced truncation recovery: production **SHIP**.
- Dual degradation still fails closed.
- 10-trial / 120-generation repeated qualification: 100% production SHIP recurrence, worst p95 2.837 s.
- Executive decision: **SHIP**.

## Production gate

```text
behavioral HOLD
    -> HOLD

provider error / empty response / unrecovered truncation
    -> HOLD

behavioral INVESTIGATE
    -> INVESTIGATE

behavioral SHIP + operational regression
    -> INVESTIGATE

single production SHIP
    -> requires repeated qualification

repeated behavioral + operational PASS
    -> candidate production SHIP

fault-injected recovery misses any production SLO
    -> HOLD for resilience qualification

fault-injected recovery + repeated qualification PASS
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
   ├── hedged provider routing
   │          ├── Nscale primary
   │          ├── hedge threshold
   │          └── Novita parallel fallback
   │
   ├── first complete response decision
   │          └── losing-attempt provenance retained
   │
   ├── deterministic safety gate
   ├── completeness gate
   ├── operational SLO gate
   ├── repeated-run stability gate
   ├── fault-injection qualification
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
├── fault_injection_latest.json
├── hedged_requests_latest.json
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
- [`docs/PHASE_1_3_LATENCY_AND_CALIBRATION.md`](docs/PHASE_1_3_LATENCY_AND_CALIBRATION.md)
- [`docs/PHASE_1_4_PRODUCTION_CONFIDENCE.md`](docs/PHASE_1_4_PRODUCTION_CONFIDENCE.md)
- [`docs/PHASE_1_4_RESULT.md`](docs/PHASE_1_4_RESULT.md)
- [`docs/PHASE_1_5_PROVIDER_RESILIENCE.md`](docs/PHASE_1_5_PROVIDER_RESILIENCE.md)
- [`docs/PHASE_1_5_RESULT.md`](docs/PHASE_1_5_RESULT.md)
- [`docs/PHASE_1_6_FAULT_INJECTION.md`](docs/PHASE_1_6_FAULT_INJECTION.md)
- [`docs/PHASE_1_6_RESULT.md`](docs/PHASE_1_6_RESULT.md)
- [`docs/PHASE_1_7_HEDGED_REQUESTS.md`](docs/PHASE_1_7_HEDGED_REQUESTS.md)
- [`docs/PHASE_1_7_RESULT.md`](docs/PHASE_1_7_RESULT.md)
- [`evals/scenarios/hia_bench_v0_1.jsonl`](evals/scenarios/hia_bench_v0_1.jsonl)

## Next qualification milestone

**Phase 1.8 — Adaptive Hedging & Cost-Aware Routing:** replace the fixed hedge delay with a policy derived from observed latency distributions and request risk, quantify redundant-token/cost overhead, test whether critical and non-critical scenarios should use different hedge thresholds, and add a dedicated-endpoint leg only after infrastructure is explicitly provisioned.

After infrastructure resilience is production-qualified across cost and latency trade-offs, Phase 2 moves into governed longitudinal memory and relationship-safety evaluation.

## Scientific and safety boundaries

HIA-Bench is a synthetic engineering benchmark. It does **not** diagnose medical or mental-health conditions, establish ground-truth user emotion, clinically validate a product, claim consciousness/AGI, or replace independent human review for high-risk deployments. Results are scoped to the tested benchmark, model, policy, provider routes, generation configuration, injected-fault model, hedge strategy, and observation window.

## License

MIT. Benchmark scenarios are synthetic and provided for research, evaluation, and engineering use.
