# Phase 1.8 Result — Adaptive Hedging & Cost-Aware Routing

## Executive verdict

**SHIP** for the tested configuration and observation window.

Scope:
- model: `meta-llama/Llama-3.1-8B-Instruct`
- primary routed provider: Nscale
- fallback routed provider: Novita
- benchmark: HIA-Bench v0.1 risk-balanced evaluation cohort
- policy: risk-aware system prompt
- unchanged production SLOs: mean latency <= 5 s, p95 latency <= 8 s
- dedicated endpoint: **NOT_CONFIGURED** and not release-critical

This result does not claim universal provider/model safety or performance. It is the qualification result for the exact tested stack above.

## Authoritative adaptive policy

The hedge schedule is derived from a fresh measured primary-route latency distribution rather than from one fixed delay:

| Risk level | Derived hedge delay |
|---|---:|
| critical | 1223.45 ms |
| high | 1323.25 ms |
| medium | 1504.93 ms |
| low | 2104.65 ms |

Critical traffic therefore receives speculative fallback earlier than ordinary traffic, while low-risk requests allow the primary route more time to complete without duplicate inference.

The fallback request timeout is also derived from the unchanged 8 s p95 contract. For the authoritative run it was **6.276 s**, computed from the p95 budget after subtracting the critical hedge delay and a 500 ms safety margin. The configured value is floored rather than rounded upward so the transport budget cannot exceed the reserved envelope by construction.

## Adaptive vs fixed 1.5 s hedge

Both policies met the production gate in the healthy 24-case comparison, but adaptive routing reduced duplicated work substantially.

| Metric | Adaptive | Fixed 1.5 s |
|---|---:|---:|
| Production decision | SHIP | SHIP |
| Scenario count | 24 | 24 |
| Hedge rate | 29.17% | 33.33% |
| Fallback winner rate | 0% | 0% |
| Winner tokens | 6,787 | 6,822 |
| Total observed tokens | 8,243 | 9,737 |
| Redundant tokens | **1,456** | 2,915 |
| Redundant-token rate | **17.66%** | 29.94% |
| Winner cost | $0.00040722 | $0.00040932 |
| Total observed cost | **$0.00046343** | $0.00052420 |
| Redundant cost | **$0.00005621** | $0.00011488 |
| Redundant-cost rate | **12.13%** | 21.92% |

Pricing is a dated engineering snapshot used only for this experiment. It is not treated as a permanent provider price guarantee.

The release gate remains lexicographic: lower cost cannot compensate for blockers, final provider errors, truncation, or SLO failure.

## Repeated critical fault recovery

The primary Nscale route was deliberately forced into a 4 s timeout for critical scenarios. The backup Novita route was launched at the measured critical hedge threshold rather than waiting for the primary timeout to expire.

Three independent fault-recovery trials were required to pass. Every trial achieved production SHIP, zero provider errors, and the unchanged latency SLOs.

| Trial | Production | Mean latency | p95 latency | Final provider errors |
|---|---|---:|---:|---:|
| 1 | SHIP | 2219.51 ms | 2463.75 ms | 0 |
| 2 | SHIP | 2637.61 ms | 5113.90 ms | 0 |
| 3 | SHIP | 2272.32 ms | 2624.08 ms | 0 |

**Critical fault recovery: 3/3 trials passed.**

This supersedes the first Phase 1.8 fault run, where one Novita fallback request hit its own 4 s `ReadTimeout` and correctly forced an executive HOLD. That earlier run is retained as engineering evidence because it motivated the SLO-derived fallback deadline; it is not the authoritative Phase 1.8 result.

## Healthy repeated qualification

The adaptive route also passed the repeated healthy-route production-confidence study:

- repeated qualification: **stable**
- behavioral and production gates remained release-eligible
- blockers: zero in the qualified runs
- final provider errors: zero in the qualified runs
- unrecovered truncations: zero in the qualified runs

The purpose of the repeated study is to prevent one favorable latency sample from being treated as production confidence.

## Release contract

Phase 1.8 keeps the same contract established in earlier phases:

```text
behavioral SHIP
0 blockers
0 unrecovered truncations
0 final provider errors
mean latency <= 5 s
p95 latency <= 8 s
```

No threshold was relaxed to obtain SHIP.

## Infrastructure status

- routed adaptive inference: **MEASURED**
- dedicated endpoint: **NOT_CONFIGURED**
- dedicated endpoint release-critical: **false**

No paid dedicated infrastructure was provisioned implicitly. A routed-vs-dedicated bakeoff remains available once a dedicated endpoint is explicitly provisioned.

## Evidence

Authoritative machine-readable evidence is published as:

`runs/adaptive_hedging_latest.json`

in the Human Intelligence Assurance Lab Hugging Face Dataset and storage bucket, with the corresponding GitHub Actions artifact retained by the qualification workflow.

## Engineering conclusion

Phase 1.8 advances the routing architecture from a fixed hedge constant to a measured, risk-aware control policy. The important result is not merely lower latency: critical traffic receives earlier resilience, ordinary traffic avoids unnecessary duplication, duplicate token/cost overhead is measured explicitly, and provider-fault recovery remains subject to the same behavioral and operational release gates.
