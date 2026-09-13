# Human Intelligence Assurance Lab

**Production architecture for measurable, safe, emotionally aware, human-centered AI.**

[![CI](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml)
[![Phase 1.8 Adaptive Hedging](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/adaptive-hedging.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/adaptive-hedging.yml)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/h0000w/Human-Intelligence-Assurance-Lab)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-yellow)](https://huggingface.co/spaces/h0000w/Human-Intelligence-Assurance-Lab)

> **Independent research and engineering portfolio project.** This repository is inspired by publicly described human-centered AI product directions. It does not use proprietary BalanX-Bio data, source code, models, confidential information, or internal architecture.

## What HIA-Lab proves

Emotionally aware and longitudinal AI should not be released because it merely *sounds* empathetic. HIA-Lab converts human-centered requirements into executable benchmark contracts, deterministic safety gates, real-model evidence, controlled model/policy/provider experiments, operational SLOs, repeated-run qualification, fault injection, adaptive routing, semantic-calibration workflows, and reproducible release lineage.

The project deliberately allows later evidence to overturn earlier positive results. A fast or high-scoring configuration can never compensate for a blocker, incomplete response, missing evidence, or failed production SLO.

## Current production evidence — Phase 1.8

Phase 1.8 replaces Phase 1.7's fixed 1.5-second hedge with a **risk-aware adaptive hedge policy derived from a freshly measured Nscale latency distribution**. Critical requests hedge earlier; low-risk requests wait longer to reduce duplicate inference. Release eligibility and routing efficiency remain separate: cost savings can never override a blocker, truncation, provider error, or latency-SLO failure.

### Adaptive hedge schedule

Authoritative measured schedule:

| Risk level | Hedge delay |
|---|---:|
| critical | **1.223 s** |
| high | **1.323 s** |
| medium | **1.505 s** |
| low | **2.105 s** |

The Novita fallback request deadline is also derived from the unchanged **8-second p95 production envelope**. In the authoritative run it was **6.276 s**, leaving a 500 ms safety margin after the measured critical hedge delay. The derived transport deadline is floored rather than rounded upward.

### Adaptive vs fixed 1.5-second hedging

Both configurations achieved production **SHIP** in the healthy 24-case comparison, but the adaptive policy materially reduced duplicate work.

| Metric | Adaptive | Fixed 1.5 s |
|---|---:|---:|
| Production | **SHIP** | **SHIP** |
| Hedge rate | **29.17%** | 33.33% |
| Winner tokens | **6,787** | 6,822 |
| Observed tokens | **8,243** | 9,737 |
| Redundant tokens | **1,456** | 2,915 |
| Redundant-token rate | **17.66%** | 29.94% |
| Winner cost | **$0.00040722** | $0.00040932 |
| Observed cost | **$0.00046343** | $0.00052420 |
| Redundant cost | **$0.00005621** | $0.00011488 |
| Redundant-cost rate | **12.13%** | 21.92% |

Pricing is a dated engineering snapshot for the tested Hugging Face routes, not a permanent provider-price claim.

### Repeated forced critical timeout recovery

The primary Nscale route was deliberately forced to consume a 4-second timeout for critical scenarios. Novita launched at the measured critical hedge threshold instead of waiting for the full primary timeout.

Three independent critical-fault trials were required to pass:

| Trial | Production | Mean | p95 | Final provider errors |
|---:|---|---:|---:|---:|
| 1 | **SHIP** | 2.220 s | 2.464 s | 0 |
| 2 | **SHIP** | 2.638 s | 5.114 s | 0 |
| 3 | **SHIP** | 2.272 s | 2.624 s | 0 |

**Critical fault recovery: 3/3 SHIP.** No release threshold was relaxed.

The first Phase 1.8 fault run is intentionally retained as superseded evidence: one real Novita fallback request hit its own 4-second `ReadTimeout`, which correctly produced an executive **HOLD**. Phase 1.8.1 hardened the architecture by deriving the fallback request budget from the unchanged p95 SLO and repeating the recovery experiment rather than rerolling a single case.

### Healthy repeated qualification

The adaptive configuration also passed repeated healthy-route qualification. This keeps the same principle introduced in Phase 1.4: one favorable run is not production confidence.

**Phase 1.8 executive decision: SHIP** for the tested model, providers, policy, benchmark, generation configuration, injected-fault model, and observation window.

### Routed vs dedicated infrastructure

Routed adaptive inference is **MEASURED**. Dedicated inference remains **NOT_CONFIGURED** and non-release-critical because no endpoint was explicitly provisioned.

HIA-Lab does not silently create billable infrastructure. Once a dedicated endpoint is explicitly available, it can be evaluated against the same benchmark, model, policy, evaluator, fault scenarios, and SLO contract.

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

### Phase 1.7 — Hedged Requests
- Controlled 0.5 / 1.0 / 1.5 / 2.0 s hedge-threshold bakeoff.
- 1.5 s selected in the measured run.
- Forced 4-second timeout recovery: 2.762 s mean / 3.604 s p95, production **SHIP**.
- Forced truncation recovery: production **SHIP**.
- Dual degradation still fails closed.
- 10-trial / 120-generation repeated qualification: 100% production SHIP recurrence, worst p95 2.837 s.
- Executive decision: **SHIP**.

### Phase 1.8 — Adaptive Hedging & Cost-Aware Routing
- Hedge timing derived from the measured primary-route latency distribution and scenario risk.
- Critical/high/medium/low hedge delays: 1.223 / 1.323 / 1.505 / 2.105 s in the authoritative run.
- Adaptive healthy route: production **SHIP**.
- Duplicate-token rate reduced from 29.94% fixed to **17.66% adaptive** in the measured comparison.
- Redundant cost reduced from $0.00011488 fixed to **$0.00005621 adaptive**.
- SLO-derived Novita fallback request budget: 6.276 s while retaining the same 8 s end-to-end p95 gate.
- Repeated forced critical primary-timeout recovery: **3/3 production SHIP**, zero final provider errors.
- Repeated healthy qualification: stable.
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

routing cost / duplicate-work evidence
    -> optimization signal only; never overrides safety/SLO gates

semantic judge
    -> shadow-only until human calibration passes
```

## Architecture

```text
HIA-Bench
   │
   ├── candidate model + executable risk-aware policy
   │          ├── bounded critical-response control
   │          └── raw response + lineage
   │
   ├── adaptive hedged provider routing
   │          ├── Nscale primary
   │          ├── measured latency profile
   │          ├── risk-specific hedge delay
   │          └── Novita parallel fallback
   │
   ├── first complete response decision
   │          └── losing-attempt token/cost/provenance retained
   │
   ├── deterministic safety gate
   ├── completeness gate
   ├── operational SLO gate
   ├── repeated-run stability gate
   ├── repeated fault-injection qualification
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
├── adaptive_hedging_latest.json
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
- [`docs/PHASE_1_8_ADAPTIVE_HEDGING.md`](docs/PHASE_1_8_ADAPTIVE_HEDGING.md)
- [`docs/PHASE_1_8_RESULT.md`](docs/PHASE_1_8_RESULT.md)
- [`docs/PHASE_1_8_INDEX.md`](docs/PHASE_1_8_INDEX.md)
- [`evals/scenarios/hia_bench_v0_1.jsonl`](evals/scenarios/hia_bench_v0_1.jsonl)

## Next qualification milestones

1. **Independent human semantic calibration:** collect >=20 independent labels, preserve reviewer provenance, require Cohen's kappa >= 0.70 and critical-case recall >= 0.95 before the semantic judge can become release-critical.
2. **Longer-window production confidence:** repeat qualification across time-separated observation windows to detect provider, latency, cost, and hedge-policy drift.
3. **Dedicated infrastructure bakeoff:** only after a dedicated endpoint is explicitly provisioned; compare it against routed inference under the same release contract.
4. **Phase 1 v1.0 assurance release:** freeze benchmark/evaluator/policy lineage and publish the consolidated executive assurance manifest.

After the Phase 1 assurance release, Phase 2 moves into governed longitudinal memory, privacy-preserving personalization, and relationship-safety evaluation.

## Scientific and safety boundaries

HIA-Bench is a synthetic engineering benchmark. It does **not** diagnose medical or mental-health conditions, establish ground-truth user emotion, clinically validate a product, claim consciousness/AGI, or replace independent human review for high-risk deployments. Results are scoped to the tested benchmark, model, policy, provider routes, generation configuration, injected-fault model, adaptive hedge strategy, pricing snapshot, and observation window.

## License

MIT. Benchmark scenarios are synthetic and provided for research, evaluation, and engineering use.
