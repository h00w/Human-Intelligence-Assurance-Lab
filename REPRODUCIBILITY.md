# Reproducibility

This repository implements **Production AI Evidence Contract v1** and the **Production AI Five-Level Proof Model v1**.

## Prerequisites

- Git
- Python 3.11+

Install the development environment:

```bash
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Reproduce

```bash
make reproduce
```

The command runs the same deterministic lint/test/benchmark chain used by CI, captures stdout/stderr, hashes relevant source, benchmark, policy and dependency files, records Git/runtime identity, and writes the Evidence Contract bundle under `evidence/out/current/`.

A reproduction `PASS` is **L2 — Reproducible**. It does not prove clinical validity, universal emotional ground truth, provider-wide SLOs, or a production release decision.

## Assess the five-level proof

```bash
make proof
```

The assessor verifies the public HIA-Lab Hugging Face Space, Dataset and methodology artifact in addition to the Level-2 evidence and writes `proof.json` plus `proof-summary.md`.

The generic portfolio claim is deliberately capped at **L3 — Capability-Validated**. HIA-Lab contains deeper provider-resilience and repeated-run studies, but those domain-specific `SHIP / INVESTIGATE / HOLD` results are not silently promoted into a universal Level-4/5 production claim. Dedicated inference infrastructure is also explicitly outside the current generic proof ceiling.

For a network-independent run:

```bash
make proof-offline
```

Offline assessment can establish at most L2.

See [PROOF_MODEL.md](PROOF_MODEL.md) for all five cumulative levels.

## Clean-room check

```bash
git clone https://github.com/h00w/Human-Intelligence-Assurance-Lab.git
cd Human-Intelligence-Assurance-Lab
git checkout <commit>
pip install -e '.[dev]'
make proof
cat evidence/out/current/proof-summary.md
```


## Portable proof artifact and signed provenance

Step 3 packages the proof state with `make proof-package` and verifies internal integrity with `make proof-verify`.

The archive contains the Evidence Contract, proof assessment, proof manifest, direct-dependency SPDX SBOM, provenance linkage, schemas, proof model and checksums. Trusted GitHub Actions runs additionally attach SLSA provenance, SBOM and custom proof-manifest attestations to the completed bundle.

Verify the external signature with:

```bash
gh attestation verify --owner h00w evidence/out/current/production-ai-proof-bundle.tar.gz
```

See [PROVENANCE.md](PROVENANCE.md). A valid signature proves provenance and integrity; it does not raise the five-level proof state by itself.
