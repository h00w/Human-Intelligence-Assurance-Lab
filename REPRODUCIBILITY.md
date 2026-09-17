# Reproducibility

This repository implements the **Production AI Evidence Contract v1**.

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

The command runs the same deterministic lint/test/benchmark chain used by CI, captures stdout/stderr, hashes relevant source, benchmark, policy and dependency files, records Git/runtime identity, and writes:

```text
evidence/out/current/
├── evidence.json
├── verification.stdout.log
├── verification.stderr.log
├── checksums.sha256
└── summary.md
```

## Interpretation

A reproduction `PASS` confirms the repository's configured verification chain passed for the recorded commit/environment. It does **not** prove clinical validity, universal emotional ground truth, provider-wide SLOs, or a production release decision.

HIA-Lab's domain-specific `SHIP / INVESTIGATE / HOLD` decisions remain separate and must be supported by the corresponding behavioral, repeated-run, operational and fault-injection evidence.

## Clean-room check

```bash
git clone https://github.com/h00w/Human-Intelligence-Assurance-Lab.git
cd Human-Intelligence-Assurance-Lab
git checkout <commit>
pip install -e '.[dev]'
make reproduce
cat evidence/out/current/summary.md
```
