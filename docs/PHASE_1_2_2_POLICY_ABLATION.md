# Phase 1.2.2 — Executable Policy Injection Ablation

The model bakeoff showed that `meta-llama/Llama-3.1-8B-Instruct` outperformed the Granite baseline on deterministic HIA-Bench pass rate and eliminated truncation, but still failed one critical vulnerability scenario because it did not escalate to human/crisis support.

Phase 1.2.2 tests whether **orchestration policy**, rather than another model swap, closes that safety gap.

## Controlled experiment

The experiment holds constant:

- model: `meta-llama/Llama-3.1-8B-Instruct`
- provider: DeepInfra through Hugging Face Inference Providers
- benchmark: same 12-case HIA-Bench canary
- generation parameters: max_tokens 512, temperature 0.2, top_p 0.9
- deterministic evaluator and release gate

Only the system-policy layer changes:

1. **Generic policy** — the standard human-centered system prompt.
2. **Risk-aware policy** — the same prompt plus executable domain/risk overlays.

## Critical vulnerability overlay

For critical vulnerability scenarios, the risk-aware policy requires the assistant to:

- respond supportively;
- explicitly encourage immediate contact with a trusted person or crisis support;
- direct the user to local emergency services when immediate danger may exist;
- avoid responding only with exploratory follow-up questions.

Additional domain overlays reinforce dependency, epistemic, and wellness boundaries.

## Evidence discipline

Each configuration gets a distinct prompt lineage fingerprint. Results are published to the Hugging Face Dataset, Storage Bucket, GitHub Actions artifact, and dashboard as `runs/policy_ablation_latest.json`.

A positive result demonstrates that executable orchestration policy improved behavior under this benchmark. It does not prove universal safety, clinical efficacy, or that prompting alone is sufficient for production high-risk systems.
