# Phase 1.5 Result — Provider Resilience & Critical-Response Control

## Executive result

**SHIP** for the measured Phase 1.5 qualification window.

The result is scoped to `meta-llama/Llama-3.1-8B-Instruct`, the HIA 12-case high-risk canary, the bounded risk-aware policy, Hugging Face routed inference, the tested provider routes, generation parameters, and this observation window.

## Why Phase 1.5 was required

Phase 1.4 invalidated the earlier single-run production-SHIP signal. Five fixed-route DeepInfra trials produced 0% production SHIP recurrence, median trial p95 of 20.14 s, worst p95 of 41.23 s, and one critical wellness truncation. Phase 1.5 therefore changed the deployment control plane rather than weakening the release thresholds.

## Provider-route bakeoff

All provider candidates used the same model, policy, benchmark, evaluator, max-token budget, temperature, and top-p.

| Provider | Behavioral | Pass rate | Blockers | Provider errors | Truncations | Mean latency | p95 latency |
|---|---|---:|---:|---:|---:|---:|---:|
| Nscale | SHIP | 100% | 0 | 0 | 0 | 1.228 s | 2.264 s |
| Novita | SHIP | 100% | 0 | 0 | 0 | 1.647 s | 6.253 s |
| DeepInfra | SHIP | 100% | 0 | 0 | 0 | 3.861 s | 7.985 s |

All three were eligible under the single-canary provider gate. Nscale was selected because it had the lowest eligible p95 latency.

## Critical-response control

Critical scenarios now require:

- mandatory safety boundary and next action in the first two sentences;
- complete-answer target of <=120 words;
- no broad differential-diagnosis or exhaustive background lists;
- preserved uncertainty and user agency.

Critical wellness scenarios additionally front-load the non-diagnostic boundary and professional-evaluation guidance and suppress speculative diagnosis lists unless the user explicitly asks about a named condition.

This control directly addresses the Phase 1.4 `hia-089` failure mode, where a cautious but overlong wellness answer exhausted its generation budget and was correctly treated as incomplete evidence.

## Deadline-aware route

Selected route:

1. Nscale — 4 s request deadline;
2. Novita — 4 s fallback deadline.

Fallback triggers on provider exception/timeout or `finish_reason=length`. Total end-to-end latency includes every attempted route; a fallback cannot conceal delay already consumed by the primary route.

## Five-trial qualification

Five independent 12-case trials produced 60 real model generations.

| Metric | Result |
|---|---:|
| Production SHIP rate | 100% |
| Behavioral SHIP rate | 100% |
| Blocker-trial rate | 0% |
| Provider-error trial rate | 0% |
| Truncation-trial rate | 0% |
| Mean latency | 1.207 s |
| Mean latency 95% CI | 1.164–1.251 s |
| Median trial p95 | 2.106 s |
| Trial-p95 95% CI | 1.921–2.474 s |
| Worst trial p95 | 2.700 s |
| Required worst p95 | <=8.000 s |

Per-trial p95 latency:

- Trial 1: 2.267 s
- Trial 2: 2.051 s
- Trial 3: 1.864 s
- Trial 4: 2.106 s
- Trial 5: 2.700 s

Every trial was behavioral SHIP and production SHIP.

## Failover interpretation

The fallback implementation is unit-tested for both timeout recovery and truncation recovery. However, the live five-trial qualification did **not** exercise fallback: Nscale completed all 60 qualification requests before the 4-second primary deadline. Therefore:

- live evidence supports Nscale route stability for this observation window;
- live evidence supports the configured deadline-aware route contract;
- fallback recovery behavior is currently unit-test evidence, not live fault-injection evidence.

This distinction is intentionally retained in the public dashboard and README.

## Phase 1.4 → Phase 1.5 comparison

| Metric | Phase 1.4 | Phase 1.5 |
|---|---:|---:|
| Production SHIP rate | 0% | 100% |
| Behavioral SHIP rate | 80% | 100% |
| Blocker-trial rate | 20% | 0% |
| Truncation-trial rate | 20% | 0% |
| Mean latency | 6.523 s | 1.207 s |
| Median trial p95 | 20.138 s | 2.106 s |
| Worst trial p95 | 41.232 s | 2.700 s |
| Executive result | HOLD | SHIP |

This is a **system-level remediation result**, not a single-variable causal claim. Phase 1.5 changed provider routing, critical-response policy, request deadlines, and the availability of fallback. The provider bakeoff isolates route performance more cleanly; the final qualification measures the combined production configuration.

## Next evidence gap

Phase 1.6 should deliberately inject primary-route timeout, truncation, and provider failure so the fallback path is exercised in a live qualification rather than only in unit tests. It should also compare routed shared infrastructure against dedicated inference infrastructure and extend the observation window/time-of-day sampling.
