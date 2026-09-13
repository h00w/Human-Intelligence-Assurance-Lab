from __future__ import annotations

import os
import time

from huggingface_hub import InferenceClient

from .base import GenerationResult, ModelAdapter


class HuggingFaceAdapter(ModelAdapter):
    provider = "huggingface"

    def __init__(
        self,
        model: str = "ibm-granite/granite-4.2-3b",
        *,
        token: str | None = None,
        provider: str = "deepinfra",
        max_tokens: int = 1024,
        temperature: float = 1.0,
        top_p: float = 0.95,
        timeout_s: float | None = None,
        input_price_per_million: float | None = 0.03,
        output_price_per_million: float | None = 0.12,
    ) -> None:
        self.model = model
        self.routing_provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.timeout_s = timeout_s
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million
        api_key = token or os.getenv("HF_TOKEN")
        if not api_key:
            raise RuntimeError("HF_TOKEN is required for Hugging Face routed inference")
        self.client = InferenceClient(provider=provider, api_key=api_key, timeout=timeout_s)

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
            top_p=self.top_p,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        choice = response.choices[0]
        text = choice.message.content or ""
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
            metadata={
                "routing_provider": self.routing_provider,
                "finish_reason": getattr(choice, "finish_reason", None),
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "timeout_s": self.timeout_s,
            },
        )
