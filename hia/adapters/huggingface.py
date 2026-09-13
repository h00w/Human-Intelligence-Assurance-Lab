from __future__ import annotations

import os
import time

from huggingface_hub import InferenceClient

from .base import GenerationResult, ModelAdapter


class HuggingFaceAdapter(ModelAdapter):
    provider = "huggingface"

    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        *,
        token: str | None = None,
        provider: str = "auto",
        max_tokens: int = 220,
        temperature: float = 0.2,
        input_price_per_million: float | None = 0.30,
        output_price_per_million: float | None = 0.30,
    ) -> None:
        self.model = model
        self.routing_provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million
        api_key = token or os.getenv("HF_TOKEN")
        if not api_key:
            raise RuntimeError("HF_TOKEN is required for Hugging Face routed inference")
        self.client = InferenceClient(provider=provider, api_key=api_key)

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        started = time.perf_counter()
        response = self.client.chat_completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        text = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        estimated_cost_usd = None
        if (
            prompt_tokens is not None
            and completion_tokens is not None
            and self.input_price_per_million is not None
            and self.output_price_per_million is not None
        ):
            estimated_cost_usd = (
                prompt_tokens * self.input_price_per_million
                + completion_tokens * self.output_price_per_million
            ) / 1_000_000

        return GenerationResult(
            provider=self.provider,
            model=self.model,
            text=text,
            latency_ms=round(latency_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            metadata={"routing_provider": self.routing_provider},
        )
