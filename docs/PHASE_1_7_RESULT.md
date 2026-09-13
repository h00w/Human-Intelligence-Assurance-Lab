# Phase 1.7 Result — Hedged Requests & Infrastructure Bakeoff

## Executive result

**SHIP** for routed hedged inference under the tested benchmark, model, policy, providers, hedge strategy, and observation window.

Phase 1.7 directly addressed the Phase 1.6 sequential-fallback failure. The production contract was not relaxed:

- behavioral SHIP;
- 0 blockers;
- 0 unrecovered truncations;
- 0 final provider errors;
- mean latency <= 5.0 s;
- p95 latency <= 8.0 s.

## Hedge-threshold bakeoff

Same Llama 3.1 8B model, risk-aware policy, 12-case high-risk canary, Nscale primary, Novita fallback, generation budget, evaluator, and release gate.

| Hedge delay | Behavioral | Production | Mean | p95 | Hedge rate | Fallback wins |
|---:|---|---|---:|---:|---:|---:|
| 0.5 s | SHIP | SHIP | 1.194 s | 1.779 s | 100% | 0% |
| 1.0 s | SHIP | SHIP | 1.240 s | 2.306 s | 66.67% | 0% |
| **1.5 s** | **SHIP** | **SHIP** | **1.137 s** | **1.589 s** | **8.33%** | **0%** |
| 2.0 s | SHIP | SHIP | 1.301 s | 2.781 s | 8.33% | 0% |

**Selected hedge delay: 1.5 s.** It had the lowest eligible p95 in this run while avoiding the very high duplicate-request rate seen at shorter thresholds.

## Forced primary timeout recovery

Nscale was forced to consume the complete 4.0-second primary timeout while the Novita fallback was launched after the selected 1.5-second hedge threshold.

| Metric | Result |
|---|---:|
| Behavioral decision | **SHIP** |
| Production decision | **SHIP** |
| Pass rate | **100%** |
| Blockers | **0** |
| Final provider errors | **0** |
| Unrecovered truncations | **0** |
| Mean decision latency | **2.762 s** |
| p95 decision latency | **3.604 s** |
| Hedge rate | **100%** |
| Fallback winner rate | **100%** |

This closes the Phase 1.6 failure: sequential timeout recovery averaged 5.252 s, while hedged timeout recovery averaged 2.762 s under the same 5-second mean SLO and 8-second p95 SLO.

Decision latency measures time to the first complete response. During qualification, the losing primary is still observed to completion so attempt provenance can be retained; that post-decision evidence collection is not charged to user-visible latency.

## Forced truncation recovery

The primary route was allowed to generate and then marked incomplete. The hedged fallback produced the complete winning response.

| Metric | Result |
|---|---:|
| Behavioral decision | **SHIP** |
| Production decision | **SHIP** |
| Mean decision latency | **2.426 s** |
| p95 decision latency | **3.352 s** |
| Hedge rate | **100%** |
| Fallback winner rate | **100%** |
| Blockers / final errors / unrecovered truncations | **0 / 0 / 0** |

## Simultaneous route degradation

Injected failure of both Nscale and Novita correctly produced **HOLD**. Hedging does not convert missing evidence into a releaseable response.

## Extended qualification

The selected 1.5-second hedge configuration was then run for **10 independent trials × 12 high-risk scenarios = 120 real generations**.

| Metric | Result |
|---|---:|
| Production SHIP recurrence | **100%** |
| Behavioral SHIP recurrence | **100%** |
| Blocker-trial rate | **0%** |
| Provider-error trial rate | **0%** |
| Truncation-trial rate | **0%** |
| Mean latency | **1.217 s** |
| Mean-latency 95% CI | **1.169–1.265 s** |
| Median trial p95 | **1.866 s** |
| Trial-p95 95% CI | **1.738–2.250 s** |
| Worst observed trial p95 | **2.837 s** |
| Stability verdict | **PASS** |

## Dedicated infrastructure

Routed hedged inference is **MEASURED**. Dedicated inference remains **NOT_CONFIGURED** because no endpoint was explicitly provisioned.

HIA-Lab does not silently create billable infrastructure. Dedicated inference is non-release-critical until a real endpoint and provider-specific authentication path are supplied; once available, it should be evaluated against the same benchmark, model, policy, fault scenarios, and SLO contract.

## Interpretation

Phase 1.7 demonstrates that the Phase 1.6 HOLD condition was architectural rather than a reason to weaken the SLO. Starting the fallback before the primary deadline expires restored production-qualified fault recovery while preserving fail-closed behavior and auditable attempt provenance.

The remaining engineering trade-off is duplicate inference work. The selected 1.5-second threshold substantially reduced healthy-request hedge frequency compared with 0.5- and 1.0-second thresholds while maintaining lower latency in this run.
