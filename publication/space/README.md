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

Interactive control center for **HIA-Bench v0.1**, real-model release gating, repeated-run production confidence, provider resilience, and fault injection.

The Streamlit Space is multipage:

- the main dashboard exposes benchmark composition, per-domain pass rates, hard safety/privacy failures, model bakeoffs, policy ablation, latency tuning, semantic-shadow state, and **SHIP / INVESTIGATE / HOLD** decisions;
- **Production Confidence** exposes the Phase 1.4 repeated-run HOLD study and executive assurance evidence;
- **Provider Resilience** exposes the Phase 1.5 provider bakeoff and repeated production-SHIP qualification;
- **Fault Injection** exposes the authoritative Phase 1.6 live fallback tests, simultaneous-provider degradation, 10-trial stability window, and infrastructure-comparison state.

## Current result — Phase 1.6 HOLD

Phase 1.6 deliberately exercised the Phase 1.5 fallback route rather than assuming it worked.

- forced Nscale timeout → Novita fallback: 100% failover, behavioral **SHIP**, production **INVESTIGATE**, mean **5.252 s**, p95 **7.231 s**;
- forced Nscale truncation → Novita fallback: 100% failover, production **SHIP**, p95 **4.479 s**;
- simultaneous Nscale + Novita degradation: correctly **HOLD**;
- healthy route: 10 trials / 120 real generations, 100% production SHIP recurrence, zero blocker/error/truncation trials, worst p95 **2.805 s**.

The authoritative fault run charges the full **4-second primary timeout budget** before fallback. An earlier experimental run that treated the injected timeout as instantaneous is superseded. Phase 1.6 remains **HOLD** because timeout recovery mean latency exceeds the unchanged 5-second production SLO, even though p95 stays below 8 seconds.

A dedicated endpoint is currently **NOT_CONFIGURED**. HIA-Lab does not silently provision paid inference infrastructure; dedicated-vs-routed comparison remains non-release-critical until an endpoint is explicitly supplied.

## Runtime

This Space intentionally uses **Docker + CPU Basic**. The UI and deterministic evaluator do not need a local GPU; hosted model inference runs remotely through Hugging Face Inference Providers. Hugging Face ZeroGPU is Gradio-only and is therefore not compatible with this Streamlit-in-Docker deployment.

HIA-Lab uses synthetic scenarios and engineering assurance checks. It does not diagnose users, establish ground-truth emotions, claim universal model safety, or provide clinical validation. Semantic judging remains shadow-only until independently calibrated against human labels.

Source of truth: `h00w/Human-Intelligence-Assurance-Lab` on GitHub.
