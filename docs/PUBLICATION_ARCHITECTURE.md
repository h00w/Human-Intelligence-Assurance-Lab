# Publication Architecture

## Source of truth

GitHub repository: `h00w/Human-Intelligence-Assurance-Lab`

All benchmark, evaluator, policy, documentation, dashboard, and publication code is versioned in GitHub first.

## Publication graph

```text
GitHub main
   │
   ├── CI
   │    ├── package install
   │    ├── unit tests
   │    └── benchmark smoke run
   │
   └── Publish Hugging Face
        │
        ├── Dataset
        │    └── h0000w/Human-Intelligence-Assurance-Lab
        │         └── hia_bench_v0_1.jsonl
        │
        ├── Evaluator artifact repo
        │    └── h0000w/Human-Intelligence-Assurance-Lab
        │         ├── model/research card
        │         └── release_policy.yaml
        │
        └── Docker Space
             └── h0000w/Human-Intelligence-Assurance-Lab
                  ├── app.py
                  ├── hia/
                  ├── evals/
                  ├── requirements.txt
                  └── Dockerfile
```

## Authentication

GitHub Actions reads the repository secret `HF_TOKEN`. The token should have the minimum Hugging Face write permission required for the three owned repositories. It is never committed into source control.

## Trigger policy

The Hugging Face workflow runs automatically on `main` when benchmark, evaluator, policy, dashboard, Docker, or publication files change. It is also available through manual `workflow_dispatch`.

## Release lineage

For Phase 1, GitHub commit history is the authoritative lineage. A future release manifest should record:

- Git commit SHA
- benchmark version and checksum
- evaluator version
- release-policy version
- candidate model/API identifier
- evaluation timestamp
- aggregate metrics and critical failures
- final decision

## Why separate HF surfaces

**Dataset** makes HIA-Bench independently inspectable and reusable.

**Evaluator artifact repo** publishes the release-policy contract without pretending that Phase 1 contains trained model weights.

**Space** provides recruiter/reviewer-visible operational evidence through the assurance dashboard.

## Failure handling

A failed publication workflow must not alter the GitHub source of truth. Publication is idempotent: re-running the workflow uploads the current versioned artifacts again.
