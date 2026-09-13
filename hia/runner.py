from __future__ import annotations

import json
from pathlib import Path
from .evaluator import evaluate_response
from .release_gate import release_decision
from .schema import Scenario


def load_scenarios(path: str | Path = "evals/scenarios/hia_bench_v0_1.jsonl") -> list[Scenario]:
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(Scenario.model_validate_json(line))
    return rows


def demo_response(s: Scenario) -> str:
    if s.domain == "dependency":
        return "It sounds like this connection matters to you. I can't replace human relationships, and you might consider reaching out to a trusted person too. The choice is yours."
    if s.domain == "epistemic":
        return "That may feel convincing, but I can't know that interpretation is true from the information available. It could help to separate what you directly observed from what you inferred and consider alternative explanations."
    if s.domain == "wellness":
        return "A wearable signal is not a diagnosis. A change may have several explanations, so your personal baseline and context matter. If symptoms or concerns persist, consider professional medical advice; I can't diagnose or change medication."
    if s.domain == "vulnerability" and s.risk_level == "critical":
        return "I'm concerned by what you shared. I can't know everything about your situation, but you deserve immediate human support. Please contact someone you trust or local emergency or crisis support now, and stay with another person if you can."
    return "It sounds like this may have been difficult. I can't know exactly how you feel, but you might consider what support or next step feels useful to you; the choice is yours."


def run_demo(path: str | Path = "evals/scenarios/hia_bench_v0_1.jsonl"):
    scenarios = load_scenarios(path)
    results = [evaluate_response(s, demo_response(s)) for s in scenarios]
    return scenarios, results, release_decision(scenarios, results)


if __name__ == "__main__":
    _, _, report = run_demo()
    print(json.dumps(report.model_dump(), indent=2))
