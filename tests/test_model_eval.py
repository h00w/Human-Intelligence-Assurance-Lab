from hia.adapters.base import GenerationResult, ModelAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.runner import load_scenarios


class SafeAdapter(ModelAdapter):
    provider = "test"
    model = "safe-model"

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        return GenerationResult(
            provider=self.provider,
            model=self.model,
            text=(
                "I can't know exactly what this means. You might consider your options, "
                "talk with someone you trust, and use context and your baseline; this is not a diagnosis. "
                "If this is urgent, contact local emergency or crisis support."
            ),
            latency_ms=10.0,
            total_tokens=42,
            estimated_cost_usd=0.00001,
        )


def test_canary_is_balanced_across_domains():
    canary = select_canary(load_scenarios(), per_domain=2)
    assert len(canary) == 12
    assert len({scenario.domain for scenario in canary}) == 6


def test_model_run_produces_evidence_and_release_report():
    scenarios = select_canary(load_scenarios(), per_domain=1)
    report = run_model_evaluation(SafeAdapter(), scenarios)
    assert report["run"]["scenario_count"] == 6
    assert len(report["evidence"]) == 6
    assert report["run"]["provider_errors"] == 0
    assert report["release_report"]["decision"] in {"SHIP", "INVESTIGATE", "HOLD"}
