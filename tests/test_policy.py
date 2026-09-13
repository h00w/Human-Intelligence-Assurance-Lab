from hia.adapters.base import GenerationResult, ModelAdapter
from hia.model_eval import SYSTEM_PROMPT, run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.runner import load_scenarios


class PolicyTestAdapter(ModelAdapter):
    provider = "test"
    model = "policy-test-model"

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        return GenerationResult(
            provider=self.provider,
            model=self.model,
            text=(
                "I can't know exactly what this means. You can consider your options and contact someone you "
                "trust. If this is urgent, contact local emergency or crisis support. This is not a diagnosis."
            ),
            latency_ms=10.0,
            total_tokens=40,
        )


def test_critical_vulnerability_gets_escalation_overlay():
    scenario = next(
        s for s in load_scenarios() if s.domain == "vulnerability" and s.risk_level == "critical"
    )
    prompt = risk_aware_system_prompt(scenario)
    assert prompt != SYSTEM_PROMPT
    assert "crisis support" in prompt
    assert "local emergency services" in prompt


def test_everyday_affect_keeps_generic_prompt():
    scenario = next(s for s in load_scenarios() if s.domain == "everyday_affect")
    assert risk_aware_system_prompt(scenario) == SYSTEM_PROMPT


def test_policy_changes_prompt_lineage():
    scenarios = select_canary(load_scenarios(), per_domain=1)
    adapter = PolicyTestAdapter()
    generic = run_model_evaluation(adapter, scenarios)
    aware = run_model_evaluation(
        adapter,
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )
    assert generic["lineage"]["prompt_version"] != aware["lineage"]["prompt_version"]
