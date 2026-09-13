# Phase 1.6 — Fault Injection & Infrastructure Qualification

Phase 1.6 turns the Phase 1.5 failover architecture into measured resilience evidence.

## Goals

1. Deliberately force the selected primary route to fail and verify that the fallback route is exercised with real inference.
2. Inject primary truncation and verify that incomplete evidence is discarded rather than released.
3. Degrade both routes simultaneously and verify fail-closed behavior.
4. Expand healthy-route qualification from 5 to 10 repeated trials by default.
5. Add an explicit contract for comparing routed inference with a dedicated endpoint without silently provisioning paid infrastructure.

## Fault-injection model

Injected faults are deterministic and labeled. They are never mixed with natural provider failures.

- `timeout`: raises an injected timeout before the primary provider request.
- `error`: raises an injected provider-boundary error.
- `truncation`: executes the real provider call, then marks the completion as truncated so the failover layer must discard it and call the fallback.

The fallback route remains a real Hugging Face routed inference request.

## Recovery contract

A fault is considered recovered only when:

- failover is actually exercised;
- the final response is behavioral `SHIP`;
- the final response is production `SHIP`;
- blocker count is zero;
- provider-error count is zero in the final released evidence;
- truncation count is zero in the final released evidence;
- end-to-end latency remains within the unchanged production SLO.

Time already consumed by a failed/truncated primary attempt is preserved in the final latency evidence.

## Simultaneous degradation

When both primary and fallback are degraded, HIA-Lab must fail closed. The expected production decision is `HOLD`; recovery is not fabricated.

## Extended qualification

The default observation window is 10 trials × 12 high-risk scenarios = 120 real generations, using the same model, policy, benchmark, evaluator and production thresholds as Phase 1.5.

Required stability remains:

- production SHIP rate >= 95%;
- blocker-trial rate = 0%;
- provider-error trial rate = 0%;
- truncation-trial rate = 0%;
- worst observed trial p95 <= 8 seconds.

## Routed vs dedicated infrastructure

The runner records the routed-inference qualification as measured evidence. A dedicated endpoint is intentionally not provisioned automatically because that can create paid cloud capacity. If `HIA_DEDICATED_ENDPOINT_URL` is absent, the dedicated comparison is reported as `NOT_CONFIGURED` and is non-release-critical.

A later explicitly provisioned endpoint can reuse the same benchmark, policy, evaluator and SLO contract for an apples-to-apples comparison.

## Evidence

Published evidence:

- HF Dataset: `runs/fault_injection_latest.json`
- HF Storage Bucket: `runs/fault_injection_latest.json`
- GitHub Actions artifact: `hia-phase-1-6-fault-injection`

Injected-fault provenance is retained in attempt metadata so reviewers can distinguish qualification faults from real provider incidents.
