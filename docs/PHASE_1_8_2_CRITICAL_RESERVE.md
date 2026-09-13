# Phase 1.8.2 — Critical Resilience Reserve

## Why this exists

The first operational long-window baseline on 2026-09-13 found a real failure during repeated critical recovery qualification: while Nscale was intentionally unavailable, one Novita fallback request (`hia-039`) ended in `ReadTimeout`. The full operational executive verdict was therefore **HOLD** even though the healthy adaptive cohort remained SHIP.

That HOLD is preserved as historical evidence. Phase 1.8.2 is a new configuration epoch, not a rerun intended to overwrite the failure.

## Remediation

Critical scenarios now use a bounded hedge ceiling of **1000 ms**. High, medium, and low risk cohorts remain distribution-derived.

The fallback deadline is still derived from the unchanged p95 contract:

`critical hedge + fallback request budget + reserve <= 8000 ms`

For the 1000 ms critical ceiling:

`1000 + 6500 + 500 = 8000 ms`

Therefore the real fallback receives the maximum configured 6.5 s request budget while the production p95 SLO remains unchanged.

## Qualification epoch

The new longitudinal epoch is:

`critical-reserve-v1`

Artifacts are written both to the operational latest path and to an epoch-specific path. Long-window qualification aggregates only snapshots belonging to the same epoch. Previous HOLD evidence remains outside the new series and remains auditable.

## Release contract

Phase 1.8.2 only SHIPs if all of the following hold:

- healthy adaptive behavioral decision SHIP;
- blockers = 0;
- final provider errors = 0;
- unrecovered truncations = 0;
- mean latency <= 5 s;
- p95 latency <= 8 s;
- every repeated critical forced-primary-timeout trial passes;
- repeated healthy qualification remains stable.

Cost/duplicate-work evidence remains secondary and cannot override safety, completeness, or latency failures.

## Claim boundary

A successful Phase 1.8.2 run qualifies only the tested model, risk policy, Nscale/Novita routes, benchmark slice, timeout fault model, and observation window. It does not erase the prior operational HOLD, prove universal provider resilience, complete independent human calibration, or qualify dedicated infrastructure.
