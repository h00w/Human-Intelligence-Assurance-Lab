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

Interactive control center for **HIA-Bench v0.1**, real-model release gating, repeated-run production confidence, and provider resilience.

The Streamlit Space is multipage:

- the main dashboard exposes benchmark composition, per-domain pass rates, hard safety/privacy failures, model bakeoffs, policy ablation, latency tuning, semantic-shadow state, and **SHIP / INVESTIGATE / HOLD** decisions;
- **Production Confidence** exposes the Phase 1.4 repeated-run HOLD study, trial-level verdicts, latency confidence intervals, failure recurrence, executive assurance, and human-calibration state;
- **Provider Resilience** exposes the Phase 1.5 Nscale / Novita / DeepInfra bakeoff, deadline-aware route, bounded critical-response controls, repeated qualification, and the measured executive **SHIP** result.

Phase 1.5 produced five consecutive production-SHIP trials (60 real generations), 100% behavioral SHIP recurrence, zero blockers/provider errors/truncations, mean latency 1.21 s, and worst trial p95 2.70 s against the 8 s SLO. Nscale was the provider-bakeoff winner at 2.26 s p95; Novita is the configured fallback.

The live five-trial run did not need to invoke fallback: Nscale completed all 60 qualification requests before the 4-second primary deadline. Fallback recovery is unit-tested, while deliberate live fault injection remains the next evidence milestone.

## Runtime

This Space intentionally uses **Docker + CPU Basic**. The UI and deterministic evaluator do not need a local GPU; hosted model inference runs remotely through Hugging Face Inference Providers. Hugging Face ZeroGPU is Gradio-only and is therefore not compatible with this Streamlit-in-Docker deployment.

HIA-Lab uses synthetic scenarios and engineering assurance checks. It does not diagnose users, establish ground-truth emotions, claim universal model safety, or provide clinical validation. Semantic judging remains shadow-only until independently calibrated against human labels.

Source of truth: `h00w/Human-Intelligence-Assurance-Lab` on GitHub.
