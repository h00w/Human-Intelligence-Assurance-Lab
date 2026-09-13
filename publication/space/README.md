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

Interactive control center for **HIA-Bench v0.1**, real-model release gating, and repeated-run production confidence.

The Streamlit Space is multipage:

- the main dashboard exposes benchmark composition, per-domain pass rates, hard safety/privacy failures, model bakeoffs, policy ablation, latency tuning, semantic-shadow state, and **SHIP / INVESTIGATE / HOLD** decisions;
- **Production Confidence** exposes the Phase 1.4 repeated-run study, trial-by-trial behavioral/production verdicts, latency confidence intervals, failure recurrence, executive assurance decision, and human-calibration state.

The latest Phase 1.4 study intentionally reports **HOLD**: five identical production trials did not reproduce the earlier single-run latency SLO reliably, and one critical wellness response was truncated. This is presented as evidence of why repeated qualification is required, not hidden as a failed demo.

## Runtime

This Space intentionally uses **Docker + CPU Basic**. The UI and deterministic evaluator do not need a local GPU; hosted model inference runs remotely through Hugging Face Inference Providers. Hugging Face ZeroGPU is Gradio-only and is therefore not compatible with this Streamlit-in-Docker deployment.

HIA-Lab uses synthetic scenarios and engineering assurance checks. It does not diagnose users, establish ground-truth emotions, claim universal model safety, or provide clinical validation. Semantic judging remains shadow-only until independently calibrated against human labels.

Source of truth: `h00w/Human-Intelligence-Assurance-Lab` on GitHub.
