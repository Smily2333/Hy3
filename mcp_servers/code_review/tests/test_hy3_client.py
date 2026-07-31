from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from openai import APIStatusError, APITimeoutError

from hy3_code_review_mcp.config import Hy3Settings
from hy3_code_review_mcp.hy3_client import Hy3APIError, Hy3Client


class FakeCompletions:
    def __init__(self, content: str | None) -> None:
        self.content = content
        self.requests: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.requests.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class SequencedCompletions:
    def __init__(self, values: list[Any]) -> None:
        self.values = values
        self.request_count = 0

    async def create(self, **kwargs: Any) -> Any:
        del kwargs
        self.request_count += 1
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=value))])


def fake_openai(completions: FakeCompletions) -> Any:
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


@pytest.mark.asyncio
async def test_complete_calls_hy3_with_expected_parameters() -> None:
    completions = FakeCompletions('{"summary":"ok","findings":[]}')
    settings = Hy3Settings(api_key="test", reasoning_effort="high")
    client = Hy3Client(settings, client=fake_openai(completions))

    result = await client.complete(system_prompt="system", user_prompt="user")

    assert result == '{"summary":"ok","findings":[]}'
    request = completions.requests[0]
    assert request["model"] == "hy3"
    assert request["messages"][0] == {"role": "system", "content": "system"}
    assert request["messages"][1] == {"role": "user", "content": "user"}
    assert request["extra_body"] == {"chat_template_kwargs": {"reasoning_effort": "high"}}


@pytest.mark.asyncio
async def test_complete_rejects_empty_content() -> None:
    client = Hy3Client(
        Hy3Settings(api_key="test"),
        client=fake_openai(FakeCompletions(None)),
    )

    with pytest.raises(Hy3APIError, match="empty completion"):
        await client.complete(system_prompt="system", user_prompt="user")


@pytest.mark.asyncio
async def test_complete_retries_transient_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    timeout = APITimeoutError(httpx.Request("POST", "https://example.test/v1"))
    completions = SequencedCompletions([timeout, "recovered"])
    sleep = AsyncMock()
    monkeypatch.setattr("hy3_code_review_mcp.hy3_client.asyncio.sleep", sleep)
    client = Hy3Client(
        Hy3Settings(api_key="test", max_retries=1),
        client=fake_openai(completions),
    )

    result = await client.complete(system_prompt="system", user_prompt="user")

    assert result == "recovered"
    assert completions.request_count == 2
    sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_complete_does_not_retry_authentication_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("POST", "https://example.test/v1")
    response = httpx.Response(401, request=request)
    error = APIStatusError("unauthorized", response=response, body=None)
    completions = SequencedCompletions([error])
    sleep = AsyncMock()
    monkeypatch.setattr("hy3_code_review_mcp.hy3_client.asyncio.sleep", sleep)
    client = Hy3Client(
        Hy3Settings(api_key="test", max_retries=2),
        client=fake_openai(completions),
    )

    with pytest.raises(Hy3APIError, match="HTTP 401"):
        await client.complete(system_prompt="system", user_prompt="user")

    assert completions.request_count == 1
    sleep.assert_not_awaited()
