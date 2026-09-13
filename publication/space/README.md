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

Interactive control center for **HIA-Bench v0.1**, real-model release gating, repeated-run production confidence, provider resilience, fault injection, and hedged-request qualification.

The Streamlit Space is multipage:

- the main dashboard exposes benchmark composition, per-domain pass rates, hard safety/privacy failures, model bakeoffs, policy ablation, latency tuning, semantic-shadow state, and **SHIP / INVESTIGATE / HOLD** decisions;
- **Production Confidence** exposes the Phase 1.4 repeated-run HOLD study and executive assurance evidence;
- **Provider Resilience** exposes the Phase 1.5 provider bakeoff and repeated production-SHIP qualification;
- **Fault Injection** exposes the authoritative Phase 1.6 sequential-fallback HOLD study;
- **Hedged Requests** exposes the Phase 1.7 hedge-threshold bakeoff, live timeout/truncation recovery, repeated qualification, and routed-vs-dedicated infrastructure state.

## Current result — Phase 1.7 SHIP

Phase 1.6 showed that sequential recovery after a complete 4-second Nscale timeout was behaviorally safe but averaged **5.252 s**, exceeding the unchanged **5-second mean-latency SLO**. Phase 1.7 changed the routing architecture instead of relaxing the SLO.

The selected hedge threshold is **1.5 s**. Under a forced 4-second Nscale timeout, Novita was launched early and won 100% of cases:

- behavioral **SHIP**;
- production **SHIP**;
- 100% pass rate;
- 0 blockers, final provider errors, or unrecovered truncations;
- mean decision latency **2.762 s**;
- p95 decision latency **3.604 s**.

Forced truncation recovery also produced production **SHIP** at **2.426 s mean / 3.352 s p95**, while simultaneous Nscale + Novita degradation still failed closed.

The selected hedge configuration then passed **10 trials / 120 real generations** with 100% behavioral and production SHIP recurrence, zero blocker/error/truncation trials, mean latency **1.217 s**, and worst trial p95 **2.837 s**.

The threshold bakeoff also exposes duplicate-work trade-offs: 0.5 s hedged 100% of healthy requests, 1.0 s hedged 66.67%, while the selected 1.5 s threshold hedged only 8.33% in its bakeoff run.

A dedicated endpoint remains **NOT_CONFIGURED**. HIA-Lab does not silently provision paid inference infrastructure; routed-vs-dedicated comparison remains non-release-critical until an endpoint is explicitly supplied.

## Runtime

This Space intentionally uses **Docker + CPU Basic**. The UI and deterministic evaluator do not need a local GPU; hosted model inference runs remotely through Hugging Face Inference Providers. Hugging Face ZeroGPU is Gradio-only and is therefore not compatible with this Streamlit-in-Docker deployment.

HIA-Lab uses synthetic scenarios and engineering assurance checks. It does not diagnose users, establish ground-truth emotions, claim universal model safety, or provide clinical validation. Semantic judging remains shadow-only until independently calibrated against human labels.

Source of truth: `h00w/Human-Intelligence-Assurance-Lab` on GitHub.
