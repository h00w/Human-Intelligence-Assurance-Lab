# Reproducibility

Human Intelligence Assurance Lab implements **Production AI Evidence Contract v1** to make assurance results traceable to an exact repository revision, benchmark/evaluator inputs, policy/configuration, environment and verification logs.

## One-command reproduction

```bash
git clone https://github.com/h00w/Human-Intelligence-Assurance-Lab.git
cd Human-Intelligence-Assurance-Lab
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
make reproduce
```

The default path is intentionally offline and does not require `HF_TOKEN`.

## What is reproduced

`evidence/reproduction-plan.json` currently verifies:

1. the unit/assurance test suite;
2. import/compile integrity for the assurance engine and evaluator package;
3. exact SHA-256 identities for the benchmark/evaluator tree, HIA engine, configuration, human-review workflow and dependency manifest;
4. a Production AI Evidence Contract v1 bundle.

The purpose is to reproduce the declared local assurance machinery. Live-provider experiments, repeated qualification, adaptive-hedging measurements and fault-injection runs remain separate retained operational evidence because they depend on external providers and dated runtime conditions.

## Evidence output

```text
artifacts/reproduction/<UTC timestamp>-<git sha>/
├── evidence.json
├── summary.md
├── checksums.sha256
└── logs/
```

Statuses are:

- `REPRODUCED` — all declared deterministic checks passed from a clean tracked checkout;
- `PARTIAL` — checks passed but tracked local modifications were present;
- `FAILED` — a required input or verification step failed.

These statuses do not replace the HIA **SHIP / INVESTIGATE / HOLD** assurance policy. A successfully reproduced `HOLD` remains a valid reproduction result.

## Important scope boundary

HIA-Bench is synthetic and non-clinical. Reproducing the benchmark and assurance code does not establish emotional or medical ground truth, nor does it prove that the benchmark generalizes to all users or cultures.

The contract proves that the declared evidence can be reconstructed for the identified source revision.

## Verify checksums

```bash
cd artifacts/reproduction/$(cat artifacts/reproduction/LATEST)
sha256sum --check checksums.sha256
```

## Custom output location

```bash
REPRO_OUT=/tmp/hia-evidence make reproduce
```

## Clean-room evidence standard

For evidence intended for publication or citation:

1. checkout an immutable tag or full commit SHA;
2. start from a clean tracked working tree;
3. install dependencies from that revision;
4. execute `make reproduce`;
5. preserve the complete evidence directory;
6. attach live-provider evidence separately with provider/model revision, policy, benchmark version, run count, fault model and observation window.

## Contract source

The canonical schema is maintained in `h00w/model-quality-release-gate` and vendored locally at:

`evidence/production-ai-evidence-contract-v1.schema.json`

The schema hash is recorded in every generated bundle.

## Updating the plan

Update the reproduction plan whenever the benchmark, deterministic gates, release policy, human-calibration workflow or critical runtime configuration changes. Do not delete a failing check to manufacture a green result. The failure itself is part of the assurance evidence.
