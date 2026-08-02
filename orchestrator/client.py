"""Thin wrapper around the Claude API. No product-specific content here."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


class MissingAPIKeyError(RuntimeError):
    pass


API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"


@dataclass
class LLMClient:
    model: str
    api_key: str | None = None  # falls back to ANTHROPIC_API_KEY env var if unset
    _client: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        key = self.api_key or os.environ.get(API_KEY_ENV_VAR)
        if not key:
            raise MissingAPIKeyError(
                f"{API_KEY_ENV_VAR} is not set. The pipeline's generative stages "
                "(requirements, design, code, tests, risk analysis) call the "
                "Claude API and need a key. Static analysis, test execution, and "
                "evidence compilation are plain tooling and don't need one. "
                f"Set it with `export {API_KEY_ENV_VAR}=...` or in a `.env` file "
                "(see `.env.example`)."
            )
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The 'anthropic' package is required. Install it with: "
                "pip install -r orchestrator/requirements.txt"
            ) from exc
        self._client = anthropic.Anthropic(api_key=key)

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        """One system prompt, one user message, plain text back."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
