---
title: Human Intelligence Assurance Lab
emoji: 🧭
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
suggested_hardware: cpu-basic
---

# Human Intelligence Assurance Lab

Interactive control center for **HIA-Bench v0.1**, real-model release gating, repeated-run production confidence, provider resilience, fault injection, hedged recovery, and adaptive cost-aware routing.

The Streamlit Space is multipage:

- the main dashboard exposes benchmark composition, per-domain pass rates, hard safety/privacy failures, model bakeoffs, policy ablation, latency tuning, semantic-shadow state, and **SHIP / INVESTIGATE / HOLD** decisions;
- **Production Confidence** exposes the Phase 1.4 repeated-run HOLD study and executive assurance evidence;
- **Provider Resilience** exposes the Phase 1.5 provider bakeoff and repeated production-SHIP qualification;
- **Fault Injection** exposes the authoritative Phase 1.6 sequential-fallback HOLD study;
- **Hedged Requests** exposes the Phase 1.7 fixed-delay hedge bakeoff and recovery qualification;
- **Adaptive Hedging** exposes the Phase 1.8 percentile-derived risk-aware hedge schedule, adaptive-vs-fixed token/cost overhead, repeated critical timeout recovery, and dedicated-infrastructure status.

## Current result — Phase 1.8 SHIP

Phase 1.8 replaces the fixed 1.5-second hedge with a routing policy derived from the current measured Nscale latency distribution and scenario risk.

Authoritative hedge delays:

- critical: **1.223 s**
- high: **1.323 s**
- medium: **1.505 s**
- low: **2.105 s**

The Novita fallback deadline is derived from the unchanged 8-second p95 envelope. In the authoritative run it was **6.276 s**, retaining a 500 ms safety margin after the critical hedge threshold.

### Adaptive vs fixed routing

Both policies achieved production **SHIP**, but adaptive routing reduced duplicate work in the measured 24-case comparison:

- redundant-token rate: **17.66% adaptive** vs 29.94% fixed;
- redundant tokens: **1,456** vs 2,915;
- redundant cost: **$0.00005621** vs $0.00011488;
- redundant-cost rate: **12.13%** vs 21.92%.

Cost evidence is an optimization signal only. It never overrides blockers, truncations, provider errors, or operational SLO failures.

### Repeated critical primary-timeout recovery

Three independent critical-fault trials were required to pass after forcing the Nscale primary into a 4-second timeout:

- trial 1: **SHIP**, 2.220 s mean / 2.464 s p95;
- trial 2: **SHIP**, 2.638 s mean / 5.114 s p95;
- trial 3: **SHIP**, 2.272 s mean / 2.624 s p95;
- final provider errors: **0 in every trial**.

The earlier Phase 1.8 HOLD is intentionally retained as superseded evidence: one real Novita request hit its own 4-second `ReadTimeout`. The hardened qualification derives the fallback deadline from the unchanged p95 budget and repeats the fault study rather than rerolling one case.

Healthy repeated qualification also passed and remained stable.

**Phase 1.8 executive decision: SHIP** for the tested model, policy, provider routes, benchmark, configuration, pricing snapshot, injected-fault model, and observation window.

A dedicated endpoint remains **NOT_CONFIGURED**. HIA-Lab does not silently provision paid inference infrastructure; routed-vs-dedicated comparison remains non-release-critical until an endpoint is explicitly supplied.

Machine-readable evidence: `runs/adaptive_hedging_latest.json` in the HIA-Lab Dataset and storage bucket.

## Runtime

This Space intentionally uses **Docker + CPU Basic**. The UI and deterministic evaluator do not need a local GPU; hosted model inference runs remotely through Hugging Face Inference Providers. Hugging Face ZeroGPU is Gradio-only and is therefore not compatible with this Streamlit-in-Docker deployment.

HIA-Lab uses synthetic scenarios and engineering assurance checks. It does not diagnose users, establish ground-truth emotions, claim universal model safety, or provide clinical validation. Semantic judging remains shadow-only until independently calibrated against human labels.

Source of truth: `h00w/Human-Intelligence-Assurance-Lab` on GitHub.


## Five-level production-AI proof

HIA-Lab now reports portfolio proof using:

`L1 Runnable → L2 Reproducible → L3 Capability-Validated → L4 Production-Candidate → L5 Production-Validated`.

The canonical GitHub source computes the level with `make proof`. The public benchmark, methodology artifact and Docker Space support **L3 — Capability-Validated**. Domain-specific provider and resilience experiments remain visible, but they are not generalized into a Level-4/5 production claim without the corresponding deployment-scoped evidence.

Specification: https://github.com/h00w/Human-Intelligence-Assurance-Lab/blob/main/PROOF_MODEL.md
