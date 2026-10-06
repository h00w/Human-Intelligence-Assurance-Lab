# Production AI Five-Level Proof Model v1

"Reproducible" is a necessary proof state, not the final claim.

| Level | Name | Minimum proof |
|---|---|---|
| 1 | **Runnable** | Pinned source executes its configured verification entry point and records an explicit result. |
| 2 | **Reproducible** | Clean checkout passes `make reproduce`; Evidence Contract v1 records source/runtime identity, dependency/input/benchmark/policy digests, retained logs, and checksums. |
| 3 | **Capability-Validated** | Level 2 plus a versioned benchmark and independently inspectable public capability evidence such as a Hugging Face Dataset/Space. |
| 4 | **Production-Candidate** | Level 3 plus an explicit release-candidate package, deterministic release policy, machine-readable decision, and project-specific pre-deployment evidence. |
| 5 | **Production-Validated** | Level 4 plus target-environment observation, SLO/telemetry evidence, and demonstrated rollback, recovery, or incident handling. |

Levels are cumulative. Reproduction PASS is not release authorization. Public demos support Level 3 but cannot establish Levels 4-5 by themselves. Synthetic benchmarks must remain labeled synthetic. Level 5 must be scoped to an identified environment and observation window.

Run `make proof` for the online assessment or `make proof-offline` for a network-independent Levels 1-2 assessment.

Canonical model: https://github.com/h00w/model-quality-release-gate/blob/main/PROOF_MODEL.md


## L5 admission contract

L5 is governed by [Deployment Evidence & Production Observation Contract v1](DEPLOYMENT_EVIDENCE.md).

A repository can advance from L4 to L5 only when the proof engine receives governed evidence for the exact deployed subject and the contract validator confirms:

- exact deployment/source/artifact identity;
- operational environment fingerprint;
- bounded real-traffic observation window;
- telemetry provenance;
- passing blocking SLOs;
- demonstrated rollback/recovery within objective;
- explicit incident/recovery state;
- cryptographic linkage to L4 proof/release evidence;
- bounded scope, exclusions, and accountable approval.

A public demo, synthetic benchmark, signature, or successful CI run cannot satisfy L5 by itself.
