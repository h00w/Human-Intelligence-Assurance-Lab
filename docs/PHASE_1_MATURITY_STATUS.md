# Phase 1 Maturity Status

Updated from the first post-Phase-1.8 longitudinal qualification on 2026-09-13.

## Frozen Phase 1.8 release

**SHIP** remains the authoritative historical Phase 1.8 result for its tested observation window.

- GitHub Actions run: `34763385977`
- artifact: `10319148905`
- source commit: `50e3173ef0b8796466c9fe0784057a7906228218`
- publication commit: `67d4a12ddc714e08fdc538f9031fa7cb98f31ca4`
- repeated forced critical-timeout recovery: 3/3 SHIP

The frozen release evidence and later operational evidence are intentionally distinct.

## Current operational longitudinal evidence

The first maturity-window run (`34774828228`) produced:

- healthy adaptive sub-run: production **SHIP**;
- healthy adaptive mean latency: **1.351 s**;
- healthy adaptive p95 latency: **2.696 s**;
- healthy repeated qualification: stable;
- repeated critical-timeout trial 1: **SHIP**;
- repeated critical-timeout trial 2: **HOLD**, one final provider error;
- repeated critical-timeout trial 3: **SHIP**;
- full adaptive executive decision: **HOLD**.

The original long-window archiver initially looked only at the healthy adaptive sub-run and reported `WAITING`. That was a provenance defect. It has been corrected: longitudinal snapshots now follow the full executive decision and aggregate provider errors/blockers/truncations from repeated critical fault recovery.

The unfavorable operational result is retained. It is not rerolled away to preserve a green status.

## Current maturity gates

| Gate | Current state | What is required |
|---|---|---|
| Frozen Phase 1.8 qualification | **SHIP** | complete |
| Human semantic calibration | **BLOCKED** | >=20 resolved samples, >=2 independent reviewers/sample, inter-reviewer kappa >=0.70, judge-vs-human kappa >=0.70, critical-failure recall >=0.95 |
| Long-window qualification | **HOLD / accumulating** | later versioned evidence must demonstrate a mature time-separated production window after the observed resilience regression is addressed |
| Dedicated infrastructure | **NOT_CONFIGURED** | explicit endpoint + credential, then same safety/completeness/SLO qualification |
| Phase 1 v1.0 | **BLOCKED** | all required maturity gates satisfied |

## Evidence integrity rule

A historical SHIP result describes the tested observation window; it does not guarantee future provider behavior. Later operational HOLD evidence does not retroactively falsify the historical measurement, but it **does block broader maturity claims** until the regression is understood and requalified under a versioned configuration.

No human labels are fabricated, no failed operational evidence is discarded, no SLO is weakened, and no paid dedicated infrastructure is provisioned implicitly.
