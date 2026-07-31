"""Small, testable async client for Hy3's OpenAI-compatible API."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from hy3_code_review_mcp.config import Hy3Settings


class Hy3APIError(RuntimeError):
    """Raised when the Hy3 API cannot return a usable completion."""


class _ChatCompletions(Protocol):
    async def create(self, **kwargs: Any) -> Any: ...


class _Chat(Protocol):
    completions: _ChatCompletions


class _OpenAIClient(Protocol):
    chat: _Chat


class Hy3Client:
    """Call Hy3 and normalize API failures for MCP tool handlers."""

    def __init__(
        self,
        settings: Hy3Settings,
        *,
        client: _OpenAIClient | None = None,
    ) -> None:
        self.settings = settings
        self._client: _OpenAIClient = client or AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return the assistant text for one Hy3 chat-completion request."""
        attempts = self.settings.max_retries + 1
        for attempt in range(attempts):
            try:
                response = await self._client.chat.completions.create(
                    model=self.settings.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    top_p=1.0,
                    max_tokens=self.settings.max_output_tokens,
                    extra_body={
                        "chat_template_kwargs": {"reasoning_effort": self.settings.reasoning_effort}
                    },
                )
                content = response.choices[0].message.content
                if not isinstance(content, str) or not content.strip():
                    raise Hy3APIError("Hy3 returned an empty completion")
                return content.strip()
            except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
                if attempt + 1 >= attempts:
                    raise Hy3APIError(
                        f"Hy3 request failed after {attempts} attempt(s): {type(exc).__name__}"
                    ) from exc
                await asyncio.sleep(min(2**attempt, 4))
            except APIStatusError as exc:
                is_retriable = exc.status_code >= 500
                if not is_retriable or attempt + 1 >= attempts:
                    raise Hy3APIError(f"Hy3 API returned HTTP {exc.status_code}") from exc
                await asyncio.sleep(min(2**attempt, 4))
            except (AttributeError, IndexError, TypeError) as exc:
                raise Hy3APIError("Hy3 returned an unexpected response shape") from exc

        raise AssertionError("unreachable")
