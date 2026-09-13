# Phase 1.8 — Adaptive Hedging & Cost-Aware Routing

Phase 1.8 replaces the fixed 1.5-second hedge delay with a risk-aware schedule derived from measured primary-route latency. It keeps the Phase 1.7 production contract unchanged.

## Release contract

A release-critical adaptive configuration must satisfy:

- behavioral decision: `SHIP`
- blocker failures: `0`
- unrecovered truncations: `0`
- final provider errors: `0`
- mean latency: `<= 5,000 ms`
- p95 latency: `<= 8,000 ms`
- repeated qualification: stable under the same contract

Efficiency evidence never overrides safety or completeness.

## Adaptive policy

The workflow first measures Nscale on a balanced high-risk canary and freezes a latency profile for that run. Hedge delays are derived from that distribution:

- critical → primary p50
- high → primary p75
- medium → primary p90
- low → primary p95

All values are bounded to 500–2,500 ms. This intentionally hedges high-risk traffic earlier while allowing ordinary traffic more primary-route variance to reduce duplicate inference.

## Cost accounting

Every completed primary/fallback attempt records token counts and estimated provider cost when pricing evidence is available. Phase 1.8 reports:

- selected-response tokens and cost
- total observed tokens and cost across both attempts
- redundant tokens
- redundant-token rate
- redundant cost
- redundant-cost rate
- hedge rate
- fallback-winner rate

The workflow compares the adaptive policy with the Phase 1.7 fixed 1,500 ms policy. A cost regression is reported as an efficiency finding; it cannot turn a safety failure into SHIP or a safety SHIP into HOLD by itself.

## Risk cohorts

Critical, high, medium and low cohorts are reported separately. The evaluation therefore makes visible whether an aggressive critical hedge improves tail resilience at the cost of more duplicate work while ordinary traffic remains economical.

## Fault recovery

The critical cohort is also evaluated with a forced four-second Nscale timeout. Novita may launch at the risk-derived critical hedge delay. Recovery must still satisfy the unchanged production SLOs.

## Dedicated infrastructure boundary

Dedicated inference remains `NOT_CONFIGURED` and non-release-critical until explicitly provisioned. Phase 1.8 does not silently create paid infrastructure.

## Pricing snapshot

The workflow uses a dated pricing snapshot for `meta-llama/Llama-3.1-8B-Instruct` from the Hugging Face Inference Providers catalog. Pricing is evidence metadata and should be refreshed before using the experiment as a current cost forecast.
