# Phase 1.8 — Adaptive Hedging & Cost-Aware Routing

The current authoritative result is **SHIP** for the tested Llama 3.1 8B / Nscale primary / Novita fallback / HIA-Bench v0.1 configuration.

The Space now includes an **Adaptive Hedging** page showing:
- percentile-derived hedge delays by risk level,
- adaptive versus fixed 1.5 s routing,
- redundant tokens and estimated cost,
- repeated critical primary-timeout recovery,
- healthy repeated qualification,
- unchanged release contract,
- dedicated infrastructure status.

Machine-readable evidence: `runs/adaptive_hedging_latest.json` in the HIA-Lab Dataset and storage bucket.

The earlier Phase 1.8 HOLD caused by one fallback ReadTimeout is intentionally retained as superseded engineering evidence; the hardened repeated recovery qualification is authoritative.
