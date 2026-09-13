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

Interactive Phase 1 control center for **HIA-Bench v0.1** and the Emotional Intelligence Release Gate.

The dashboard exposes benchmark composition, per-domain pass rates, hard safety failures, privacy failures, real-model canary evidence, and the final **SHIP / INVESTIGATE / HOLD** release decision.

## Runtime

This Space intentionally uses **Docker + CPU Basic**. The UI and deterministic evaluator do not need a local GPU; hosted model inference runs remotely through Hugging Face Inference Providers. Hugging Face ZeroGPU is Gradio-only and is therefore not compatible with this Streamlit-in-Docker deployment.

Phase 1 uses synthetic text scenarios and auditable deterministic checks. It does not diagnose users, infer ground-truth emotions, or claim clinical validation.

Source of truth: `h00w/Human-Intelligence-Assurance-Lab` on GitHub.
