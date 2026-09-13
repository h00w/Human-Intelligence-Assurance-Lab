# Phase 1.7 — Hedged Requests & Dedicated Infrastructure Bakeoff

Phase 1.7 addresses the remaining Phase 1.6 failure without weakening the production contract.

Phase 1.6 proved that sequential fallback recovered availability and safety after a forced four-second primary timeout, but the recovered path averaged 5.252 seconds and therefore exceeded the unchanged 5-second mean-latency SLO.

## Hypothesis

Launch the fallback route before the primary deadline expires. If the primary is still incomplete at the hedge threshold, run the fallback concurrently and accept the first complete response. This should reduce user-visible recovery latency while retaining complete attempt provenance.

## Release contract

Phase 1.7 retains the same release-critical targets:

- behavioral decision: SHIP;
- blocker failures: 0;
- unrecovered truncations: 0;
- final provider errors: 0;
- mean latency <= 5,000 ms;
- p95 latency <= 8,000 ms.

A fast fallback cannot compensate for an unsafe or incomplete response.

## Decision latency and provenance

User-visible decision latency is wall-clock time from request start until the first non-empty, non-truncated response completes.

During qualification, an already-running losing attempt is allowed to finish so HIA-Lab can record:

- route role and provider;
- launch and completion times;
- finish reason;
- token usage;
- estimated cost when pricing is configured;
- whether the attempt completed after the release decision;
- whether a fault was injected.

That post-decision evidence collection is not charged to decision latency. In production, the losing request may be cancelled when the transport supports cancellation; otherwise its result is ignored.

## Controlled experiments

1. Hedge-threshold bakeoff over 500 / 1,000 / 1,500 / 2,000 ms by default.
2. Forced four-second Nscale timeout with real Novita fallback launched at the selected hedge threshold.
3. Forced Nscale truncation with real Novita fallback.
4. Simultaneous primary + fallback degradation, which must fail closed.
5. Ten repeated healthy-route trials across the same 12-case high-risk canary.
6. Routed-versus-dedicated infrastructure comparison contract.

## Dedicated infrastructure

No paid endpoint is provisioned implicitly. Until `HIA_DEDICATED_ENDPOINT_URL` is explicitly supplied and an authenticated endpoint adapter is configured, dedicated infrastructure remains `NOT_CONFIGURED` and non-release-critical.

## Executive SHIP

Phase 1.7 can SHIP only if:

- at least one hedge threshold satisfies all behavioral and operational gates;
- forced timeout recovery satisfies all release gates;
- forced truncation recovery satisfies all release gates;
- simultaneous route degradation fails closed;
- repeated healthy-route qualification is stable.

The dedicated endpoint bakeoff does not affect this decision until infrastructure has been explicitly provisioned.
