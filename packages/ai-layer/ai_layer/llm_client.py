"""
ai_layer/llm_client.py
Production LLM transport. The only module in the codebase that knows OpenAI exists.

Interface contract with explain.py: a single ``.call(system, user) -> str``.
Everything else here is about staying inside the /explain latency budget and
never being the reason the endpoint returns 5xx.

Design notes, each one a bug this file is written to avoid:

  * Construction is lazy and defensive. Reading OPENAI_API_KEY at import time
    with os.environ["..."] turns a missing Railway variable into an ImportError
    that takes down the whole FastAPI app, including /health.
  * Deadline, not timeout. The SDK default is 600 s against a 3 s SLA. This
    client tracks a wall-clock deadline derived from shared_types.sla and will
    not start an attempt it cannot finish.
  * Retries only on transient errors, and only with budget left.
  * temperature=0. Identical input must produce identical explanation, or the
    eval suite measures noise and support cannot reproduce a user's screen.
  * Usage and timing come back with the result, so fallback_rate, p95 latency
    and cost per call are measured rather than estimated.
"""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import asdict, dataclass
from typing import Optional

from shared_types.sla import llm_attempt_timeout_ms, llm_deadline_ms

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOKENS = 400


class LLMUnavailable(RuntimeError):
    """No usable completion. The caller must serve the deterministic template."""


@dataclass(frozen=True)
class LLMResult:
    """String-like result: explain.py reads ``.text``, telemetry reads the rest."""

    text: str
    model: str
    latency_ms: int
    attempts: int
    prompt_tokens: int
    completion_tokens: int

    def __str__(self) -> str:
        return self.text

    def as_event_payload(self) -> dict:
        return asdict(self)


class OpenAIClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        deadline_ms: Optional[int] = None,
        attempt_timeout_ms: Optional[int] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.0,
        max_attempts: int = 2,
    ) -> None:
        api_key = (api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
        if not api_key:
            raise LLMUnavailable("OPENAI_API_KEY is not set")

        try:
            import openai
        except ImportError as exc:  # pragma: no cover — depends on deployment image
            raise LLMUnavailable(f"openai package not installed: {exc}") from exc

        self._openai = openai
        # max_retries=0: retry policy lives here, where the deadline is known.
        self._client = openai.OpenAI(api_key=api_key, max_retries=0)
        self.model = model or os.environ.get("FINSIGHT_LLM_MODEL", DEFAULT_MODEL)
        self.deadline_ms = deadline_ms or int(
            os.environ.get("FINSIGHT_LLM_DEADLINE_MS", llm_deadline_ms())
        )
        self.attempt_timeout_ms = attempt_timeout_ms or llm_attempt_timeout_ms()
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_attempts = max_attempts

    # ------------------------------------------------------------------

    def _is_transient(self, exc: Exception) -> bool:
        openai = self._openai
        candidates = (
            getattr(openai, "APITimeoutError", None),
            getattr(openai, "APIConnectionError", None),
            getattr(openai, "RateLimitError", None),
            getattr(openai, "InternalServerError", None),
        )
        types = tuple(c for c in candidates if isinstance(c, type))
        return bool(types) and isinstance(exc, types)

    # ------------------------------------------------------------------

    def call(self, system_prompt: str, user_message: str) -> LLMResult:
        """Return the model's raw response.

        Does not parse, validate or check numbers — that is the validation
        gateway's job. This layer owns transport, timing and degradation only.
        """
        # response_format=json_object is rejected unless the word "json" appears
        # in the conversation. Failing here is far cheaper than a 400 per request
        # discovered in production.
        if "json" not in (system_prompt + user_message).lower():
            raise LLMUnavailable(
                "response_format=json_object requires the word 'json' in the prompt"
            )

        started = time.monotonic()
        deadline = started + self.deadline_ms / 1000
        last_error: Optional[BaseException] = None

        for attempt in range(1, self.max_attempts + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0.2:
                break

            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=min(self.attempt_timeout_ms / 1000, remaining),
                )
            except Exception as exc:  # noqa: BLE001 — only LLMUnavailable escapes
                last_error = exc
                if not self._is_transient(exc) or attempt >= self.max_attempts:
                    break
                backoff = min(
                    0.15 + random.random() * 0.15,
                    max(deadline - time.monotonic() - 0.2, 0.0),
                )
                if backoff <= 0:
                    break
                time.sleep(backoff)
                continue

            choice = response.choices[0]
            text = (choice.message.content or "").strip()

            if choice.finish_reason == "length":
                # Truncated JSON cannot pass the gate; a clean fallback beats
                # feeding the validator a fragment.
                last_error = LLMUnavailable("completion truncated (max_tokens)")
                break

            if not text:
                last_error = LLMUnavailable("empty completion")
                if attempt >= self.max_attempts:
                    break
                continue

            usage = getattr(response, "usage", None)
            return LLMResult(
                text=text,
                model=self.model,
                latency_ms=int((time.monotonic() - started) * 1000),
                attempts=attempt,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            )

        raise LLMUnavailable(
            f"no usable completion after {self.max_attempts} attempt(s): "
            f"{type(last_error).__name__ if last_error else 'deadline'}: {last_error}"
        )
