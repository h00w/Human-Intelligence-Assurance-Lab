from __future__ import annotations

import json
import time
from urllib import request

from .base import GenerationResult, ModelAdapter


class DedicatedEndpointAdapter(ModelAdapter):
    """OpenAI-compatible dedicated endpoint adapter.

    This adapter performs no provisioning. It is only usable when an explicit endpoint URL
    and credential have already been supplied by the operator.
    """

    provider = "dedicated"

    def __init__(
        self,
        *,
        endpoint_url: str,
        api_key: str,
        model: str,
        timeout_s: float = 8.0,
        max_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> None:
        if not endpoint_url.strip():
            raise ValueError("dedicated endpoint URL is required")
        if not api_key.strip():
            raise ValueError("dedicated endpoint API key is required")
        self.endpoint_url = endpoint_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p

    def generate(self, *, system_prompt: str, user_prompt: str) -> GenerationResult:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }
        ).encode("utf-8")
        req = request.Request(
            self.endpoint_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        started = time.perf_counter()
        with request.urlopen(req, timeout=self.timeout_s) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        latency_ms = (time.perf_counter() - started) * 1000
        choice = payload["choices"][0]
        usage = payload.get("usage", {})
        return GenerationResult(
            provider=self.provider,
            model=self.model,
            text=choice["message"]["content"],
            latency_ms=round(latency_ms, 2),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            metadata={
                "endpoint_class": "dedicated",
                "finish_reason": choice.get("finish_reason"),
                "provisioned_externally": True,
            },
        )
