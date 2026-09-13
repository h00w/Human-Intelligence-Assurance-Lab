from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
ReleaseSeverity = Literal["minor", "major", "blocker"]
Decision = Literal["SHIP", "INVESTIGATE", "HOLD"]


class ScenarioInput(BaseModel):
    user_message: str
    prior_context: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=lambda: ["text"])


class EmotionalStateHypothesis(BaseModel):
    valence: str
    arousal: str
    distress: float = Field(ge=0, le=1)
    uncertainty: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class ScenarioMetadata(BaseModel):
    synthetic: bool = True
    medical_ground_truth: bool = False
    human_review_required: bool = False


class Scenario(BaseModel):
    id: str
    version: str
    domain: str
    risk_level: RiskLevel
    input: ScenarioInput
    emotional_state_hypothesis: EmotionalStateHypothesis
    expected_behaviors: list[str]
    forbidden_behaviors: list[str]
    release_severity: ReleaseSeverity
    metadata: ScenarioMetadata


class EvaluationResult(BaseModel):
    scenario_id: str
    domain: str
    risk_level: RiskLevel
    scores: dict[str, float]
    violations: list[str] = Field(default_factory=list)
    passed: bool


class ReleaseReport(BaseModel):
    decision: Decision
    total_cases: int
    pass_rate: float
    critical_failures: int
    blocker_failures: int
    privacy_violations: int
    dependency_failures: int
    health_boundary_failures: int
    domain_pass_rates: dict[str, float]
    reasons: list[str]
