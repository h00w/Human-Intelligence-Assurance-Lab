# Phase 1 Maturity Gates

Phase 1.8 closed the adaptive routing and cost-aware resilience work with an authoritative **SHIP**. Phase 1 is not yet declared fully mature or released as v1.0 because three independent evidence classes remain.

## Gate A — Human semantic calibration

Status: **BLOCKED ON INDEPENDENT HUMAN LABELS**.

Engineering contract:
- >=20 resolved samples;
- >=2 independent reviewers per sample;
- reviewer provenance required;
- explicit adjudication for disagreements;
- inter-reviewer kappa >=0.70;
- judge-vs-human kappa >=0.70;
- critical-failure recall >=0.95.

No automated process may fabricate these labels.

## Gate B — Longer-window production qualification

Status: **ACCUMULATING EVIDENCE**.

A maturity-qualified window requires:
- >=3 independent qualification snapshots;
- >=7 days between first and latest snapshot;
- 100% production SHIP across the accepted windows;
- zero blockers, final provider errors, and unrecovered truncations;
- mean latency <=5 s and p95 <=8 s in every window.

`Long-Window Qualification` archives a dated adaptive-routing result weekly. Insufficient history returns `WAITING`; an actual contract regression returns `HOLD`.

## Gate C — Dedicated infrastructure qualification

Status: **NOT_CONFIGURED**.

The repository now contains an OpenAI-compatible dedicated-endpoint adapter and a manual qualification workflow. It performs no provisioning. The workflow contacts a dedicated endpoint only after both `HIA_DEDICATED_ENDPOINT` and `HIA_DEDICATED_API_KEY` are explicitly configured.

A dedicated endpoint must pass the same behavioral, completeness, mean-latency and p95-latency contract as routed inference before this gate becomes `QUALIFIED`.

## Gate D — v1.0 release readiness

The consolidated v1 readiness gate is intentionally strict:

```text
Phase 1.8 authoritative SHIP
AND independent human semantic calibration PASS
AND long-window qualification PASS
AND dedicated infrastructure QUALIFIED
    -> READY

missing evidence without a failed contract
    -> BLOCKED

failed required production contract
    -> HOLD
```

Current expected state: **BLOCKED**. This is an evidence state, not a failure of Phase 1.8.

Once all four gates are satisfied, the final release step is to freeze benchmark/evaluator/policy lineage, publish the executive assurance manifest, create the v1.0 GitHub release, update Hugging Face cards, and then begin Phase 2: governed longitudinal memory, privacy-preserving personalization, and relationship-safety evaluation.
