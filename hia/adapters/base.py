from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GenerationResult:
    provider: str
    model: str
    text: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelAdapter(ABC):
    provider: str
    model: str

    @abstractmethod
    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        """Generate a single response and return auditable execution metadata."""
