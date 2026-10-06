---
license: mit
library_name: hia-lab
pipeline_tag: text-classification
---

# Human Intelligence Assurance Lab — Phase 1 Evaluator Package

This Hugging Face model repository is used as the publication endpoint for the Phase 1 **evaluation and release-policy artifact**. It intentionally does **not** claim to provide trained model weights.

Published artifacts include the HIA emotional-intelligence release policy and documentation needed to reproduce SHIP / INVESTIGATE / HOLD decisions.

The reference implementation combines deterministic safety checks with benchmark metadata. Future phases may add pluggable model-based semantic judges, calibrated evaluators, and real model/API adapters.

This project is an independent engineering portfolio project and does not use proprietary BalanX-Bio data, code, models, or confidential information.


## Five-level production-AI proof

HIA-Lab now reports portfolio proof using:

`L1 Runnable → L2 Reproducible → L3 Capability-Validated → L4 Production-Candidate → L5 Production-Validated`.

The canonical GitHub source computes the level with `make proof`. The public benchmark, methodology artifact and Docker Space support **L3 — Capability-Validated**. Domain-specific provider and resilience experiments remain visible, but they are not generalized into a Level-4/5 production claim without the corresponding deployment-scoped evidence.

Specification: https://github.com/h00w/Human-Intelligence-Assurance-Lab/blob/main/PROOF_MODEL.md
