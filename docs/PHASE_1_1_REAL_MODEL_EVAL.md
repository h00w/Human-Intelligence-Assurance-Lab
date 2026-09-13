# Phase 1.1 — Real Model Evaluation

Phase 1.1 connects HIA-Bench to real hosted model outputs while preserving the Phase 1 safety contract.

## Objectives

1. Keep provider APIs behind a stable adapter interface.
2. Capture response text, latency, token usage, estimated cost, provider/model identity, and evaluation evidence.
3. Run a balanced 12-case canary (2 higher-risk cases per domain) on every relevant `main` change and on manual workflow dispatch.
4. Treat provider failures as failed evidence, never as passes.
5. Publish the latest run to the Hugging Face Dataset and mutable trace evidence to the project Storage Bucket.
6. Surface the latest real-model release decision in the public Space.

## Default candidate

The default canary model is `Qwen/Qwen2.5-7B-Instruct` through Hugging Face Inference Providers. The model id can be overridden through the workflow input.

Pricing is an estimate configured in the adapter and must be treated as operational metadata, not an invoice. Provider routing and prices can change.

## Evidence flow

```text
HIA-Bench canary
      │
      ▼
Provider adapter
      │
      ├── response
      ├── latency
      ├── token usage
      └── estimated cost
      │
      ▼
Deterministic safety evaluator
      │
      ▼
SHIP / INVESTIGATE / HOLD
      │
      ├── Dataset: versioned latest public result
      ├── Bucket: mutable run evidence
      ├── Actions: 30-day workflow artifact
      └── Space: recruiter-facing dashboard
```

## Current limitation

Phase 1.1 evaluates real model responses with the auditable deterministic evaluator from Phase 1. It does not yet claim semantic empathy measurement. A calibrated semantic judge and human-review protocol belong in the next increment and must be validated against human annotations before being used as a release-critical metric.
