---
license: mit
pretty_name: HIA-Bench v0.1
language:
- en
task_categories:
- text-classification
---

# HIA-Bench v0.1

A synthetic evaluation benchmark for emotionally aware, human-centered AI systems.

It contains 100 scenarios across six domains: everyday affect, interpersonal conflict, vulnerability/crisis, dependency risk, epistemic/sycophancy risk, and wellness/biometric interpretation.

The benchmark is designed for evaluation and release assurance. It is not a clinical dataset, does not contain real patient records, and does not establish ground-truth emotional or medical states.

Each record includes risk level, an uncertain emotional-state hypothesis, expected behaviors, forbidden behaviors, release severity, and human-review metadata.


## Five-level production-AI proof

HIA-Lab now reports portfolio proof using:

`L1 Runnable → L2 Reproducible → L3 Capability-Validated → L4 Production-Candidate → L5 Production-Validated`.

The canonical GitHub source computes the level with `make proof`. The public benchmark, methodology artifact and Docker Space support **L3 — Capability-Validated**. Domain-specific provider and resilience experiments remain visible, but they are not generalized into a Level-4/5 production claim without the corresponding deployment-scoped evidence.

Specification: https://github.com/h00w/Human-Intelligence-Assurance-Lab/blob/main/PROOF_MODEL.md
