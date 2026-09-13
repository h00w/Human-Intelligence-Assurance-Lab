# Human Intelligence Assurance Lab

**Production architecture for measurable, safe, emotionally aware, human-centered AI.**

[![CI](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/ci.yml)
[![Phase 1.6 Fault Injection](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/fault-injection.yml/badge.svg)](https://github.com/h00w/Human-Intelligence-Assurance-Lab/actions/workflows/fault-injection.yml)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/h0000w/Human-Intelligence-Assurance-Lab)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-yellow)](https://huggingface.co/spaces/h0000w/Human-Intelligence-Assurance-Lab)

> **Independent research and engineering portfolio project.** This repository is inspired by publicly described human-centered AI product directions. It does not use proprietary BalanX-Bio data, source code, models, confidential information, or internal architecture.

## What HIA-Lab proves

Emotionally aware and longitudinal AI should not be released because it merely *sounds* empathetic. HIA-Lab converts human-centered AI requirements into executable benchmark contracts, deterministic safety gates, real-model evidence, controlled model/policy/provider experiments, operational SLOs, repeated-run qualification, fault injection, semantic-calibration workflows, and reproducible release lineage.

The project deliberately allows later evidence to overturn earlier positive results. A fast or high-scoring configuration can never compensate for a safety blocker, incomplete response, missing evidence, or failed production SLO.

## Current production evidence — Phase 1.6

Phase 1.5 selected **Nscale** as primary and **Novita** as fallback after a controlled provider bakeoff and achieved five consecutive production-SHIP trials. Phase 1.6 then tested the assumption that fallback would remain production-grade when the primary route actually fails.

### Live fault injection

The authoritative Phase 1.6 run charges the full **4.0-second primary timeout budget** before fallback latency. An earlier experimental run that treated the synthetic timeout as instantaneous is superseded and is not used for the release conclusion.

| Fault case | Failover | Behavioral | Production | Mean | p95 | Conclusion |
|---|---:|---|---|---:|---:|---|
| Forced Nscale timeout → real Novita fallback | **100%** | **SHIP** | **INVESTIGATE** | **5.252 s** | **7.231 s** | Recovery works, mean SLO misses |
| Forced Nscale truncation → real Novita fallback | **100%** | **SHIP** | **SHIP** | **2.498 s** | **4.479 s** | PASS |
| Simultaneous Nscale + Novita degradation | attempted | HOLD | HOLD | n/a | n/a | Correct fail-closed behavior |

The timeout case successfully returned complete, behaviorally safe responses through Novita with zero final blockers, provider errors, or truncations. However, the composite production gate correctly returned **INVESTIGATE** because mean end-to-end latency was **5.252 s**, above the unchanged **5.000 s mean-latency SLO**. The p95 remained below the 8-second limit at 7.231 s.

Therefore the **Phase 1.6 executive decision is HOLD**. The SLO is intentionally not relaxed.

### Extended healthy-route qualification

The healthy Nscale → Novita route was also expanded to **10 trials × 12 high-risk cases = 120 real generations**.

| Qualification metric | Result |
|---|---:|
| Behavioral SHIP rate | **100%** |
| Production SHIP rate | **100%** |
| Blocker-trial rate | **0%** |
| Provider-error trial rate | **0%** |
| Truncation-trial rate | **0%** |
| Mean latency | **1.269 s** |
| Mean latency 95% CI | **1.241–1.296 s** |
| Median trial p95 | **2.455 s** |
| Trial-p95 95% CI | **2.088–2.649 s** |
| Worst observed trial p95 | **2.805 s** |
| Stability verdict | **PASS** |

Normal operation is stable in this observation window. Phase 1.6 remains HOLD specifically because **sequential recovery after a full 4-second timeout cannot satisfy the 5-second mean SLO**.

### Routed vs dedicated infrastructure

Routed Hugging Face inference is measured. A dedicated endpoint is currently **NOT_CONFIGURED** and is explicitly non-release-critical.

HIA-Lab does not silently provision paid infrastructure. If a dedicated endpoint is explicitly supplied later, it can be evaluated against the same model, benchmark, policy, evaluator, fault scenarios, and SLO contract.

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
- Live model bakeoff.
- Executable policy ablation.
- Composite behavioral + operational production gate.
- Semantic judge remains **shadow-only** pending independent human calibration.

Human calibration requires at least 20 genuine reviews, Cohen's kappa >=0.70, critical-failure recall >=0.95, and reviewer provenance. HIA-Lab does not fabricate human labels.

### Phase 1.3 — Single-run SLO closure
- Risk-aware Llama configuration reached 100% behavioral pass and p95 6.50 s.
- Later repeated evidence showed why one favorable run was not enough.

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
- Limitation: fallback was configured but not exercised naturally.

### Phase 1.6 — Fault Injection & Infrastructure Qualification
- Forced primary timeout with real fallback.
- Forced primary truncation with real fallback.
- Simultaneous provider degradation test.
- Full timeout-budget accounting in end-to-end latency.
- Extended 10-trial / 120-generation healthy-route qualification.
- Dedicated endpoint comparison contract without implicit paid provisioning.
- Authoritative executive decision: **HOLD**, because timeout recovery mean latency exceeds the production SLO.

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
   ├── provider routing
   │          ├── Nscale primary + deadline
   │          └── Novita fallback + attempt provenance
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
- [`docs/PHASE_1_5_RESULT.md`](docs/PHASE_1_5_RESULT.md)
- [`docs/PHASE_1_6_FAULT_INJECTION.md`](docs/PHASE_1_6_FAULT_INJECTION.md)
- [`docs/PHASE_1_6_RESULT.md`](docs/PHASE_1_6_RESULT.md)
- [`evals/scenarios/hia_bench_v0_1.jsonl`](evals/scenarios/hia_bench_v0_1.jsonl)

## Next qualification milestone

**Phase 1.7 — Hedged Requests & Dedicated Infrastructure Bakeoff:** test adaptive/hedged fallback so recovery can begin before the entire primary deadline is consumed, preserve cancellation/attempt provenance, qualify injected timeout recovery against the unchanged 5-second mean and 8-second p95 SLOs, and compare routed inference with an explicitly provisioned dedicated endpoint when one is available.

After infrastructure resilience is production-qualified, Phase 2 moves into governed longitudinal memory and relationship-safety evaluation.

## Scientific and safety boundaries

HIA-Bench is a synthetic engineering benchmark. It does **not** diagnose medical or mental-health conditions, establish ground-truth user emotion, clinically validate a product, claim consciousness/AGI, or replace independent human review for high-risk deployments. Results are scoped to the tested benchmark, model, policy, provider routes, generation configuration, injected-fault model, and observation window.

## License

MIT. Benchmark scenarios are synthetic and provided for research, evaluation, and engineering use.
