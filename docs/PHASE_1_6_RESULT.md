# Phase 1.6 — Measured Result

## Executive result: HOLD

Phase 1.6 converted the Phase 1.5 fallback assumption into live resilience evidence. The authoritative run is schema `1.6.1` and charges the full 4,000 ms primary timeout budget before fallback latency. An earlier run that treated the injected timeout as instantaneous is superseded and is not used for the release conclusion.

## Fault-injection results

| Case | Failover | Behavioral | Production | Mean latency | p95 latency | Result |
|---|---:|---|---|---:|---:|---|
| Forced Nscale timeout → real Novita fallback | 100% | SHIP | INVESTIGATE | 5.252 s | 7.231 s | Recovery works, mean SLO misses |
| Forced Nscale truncation → real Novita fallback | 100% | SHIP | SHIP | 2.498 s | 4.479 s | PASS |
| Simultaneous Nscale + Novita degradation | attempted | HOLD | HOLD | n/a | n/a | Correct fail-closed behavior |

The forced-timeout path is the only release-critical failure. All 12 responses were ultimately generated successfully by the fallback and passed behavioral safety, with zero final blockers, provider errors, or truncations. However, the composite operational gate returned `INVESTIGATE` because mean end-to-end latency was **5.252 s**, above the unchanged **5.000 s** mean-latency SLO. Its p95 of **7.231 s** remained below the 8-second p95 limit.

This is intentionally reported as a failure of production recovery latency, not hidden as successful availability recovery.

## Extended healthy-route qualification

The normal Nscale → Novita route was then evaluated over **10 trials × 12 high-risk cases = 120 real generations**.

| Metric | Result |
|---|---:|
| Production SHIP rate | 100% |
| Behavioral SHIP rate | 100% |
| Blocker-trial rate | 0% |
| Provider-error trial rate | 0% |
| Truncation-trial rate | 0% |
| Mean latency | 1.269 s |
| Mean latency 95% CI | 1.241–1.296 s |
| Median trial p95 | 2.455 s |
| Trial-p95 95% CI | 2.088–2.649 s |
| Worst observed p95 | 2.805 s |
| Stability verdict | PASS |

The healthy route is therefore stable in the evaluated window. Phase 1.6 remains HOLD specifically because forced timeout recovery cannot yet satisfy all production SLOs.

## Infrastructure qualification

Routed Hugging Face inference is measured. A dedicated inference endpoint is **NOT_CONFIGURED** and remains non-release-critical.

HIA-Lab intentionally does not provision paid dedicated infrastructure implicitly. An explicitly provisioned endpoint can later be evaluated using the same model, benchmark, executable policy, evaluator, and SLO contract.

## Engineering conclusion

Sequential failover with a 4-second primary deadline has a structural latency cost. When the primary consumes its entire deadline, the fallback only has about one second of mean-latency budget remaining before the 5-second mean SLO is violated.

The next remediation should therefore test **hedged/adaptive requests** rather than relaxing the SLO: launch a backup route before the full primary deadline when latency risk becomes high, preserve provenance/cancellation evidence, and qualify both normal and injected-failure paths under the same release gate.
