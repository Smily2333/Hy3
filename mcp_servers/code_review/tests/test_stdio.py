from __future__ import annotations

import json
import os
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = {
    "review_diff",
    "explain_changes",
    "generate_test_plan",
}


class FakeHy3Handler(BaseHTTPRequestHandler):
    """Return one deterministic OpenAI-compatible chat completion."""

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        request_body = json.loads(self.rfile.read(content_length))
        self.server.requests.append(request_body)  # type: ignore[attr-defined]

        model_content = json.dumps(
            {
                "summary": "One evidence-backed finding.",
                "findings": [
                    {
                        "severity": "high",
                        "location": "app.py:1",
                        "title": "Missing null check",
                        "problem": "The new code dereferences a nullable value.",
                        "reason": "The repository may return None.",
                        "suggestion": "Check for None before dereferencing.",
                    }
                ],
            }
        )
        response = json.dumps(
            {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 0,
                "model": "hy3",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": model_content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "total_tokens": 20,
                },
            }
        ).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format: str, *args: Any) -> None:
        del format, args


@pytest.fixture
def fake_hy3_server() -> Iterator[tuple[str, list[dict[str, Any]]]]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHy3Handler)
    server.requests = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", server.requests  # type: ignore[attr-defined]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio
async def test_stdio_lists_tools_and_calls_hy3(
    fake_hy3_server: tuple[str, list[dict[str, Any]]],
) -> None:
    base_url, requests = fake_hy3_server
    env = os.environ.copy()
    env.update(
        {
            "HY3_API_KEY": "stdio-test-key",
            "HY3_BASE_URL": base_url,
            "HY3_MAX_RETRIES": "0",
        }
    )
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "hy3_code_review_mcp"],
        cwd=PROJECT_DIR,
        env=env,
    )

    async with (
        stdio_client(server) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS

        result = await session.call_tool("review_diff", {"diff": ""})
        assert result.isError is True
        assert result.content
        assert "diff must not be empty" in result.content[0].text

        result = await session.call_tool(
            "review_diff",
            {
                "diff": "diff --git a/app.py b/app.py\n+value.run()",
                "severity_threshold": "medium",
            },
        )
        assert result.isError is False
        assert result.structuredContent is not None
        assert result.structuredContent["summary"] == "One evidence-backed finding."
        assert result.structuredContent["findings"][0]["severity"] == "high"

    assert len(requests) == 1
    assert requests[0]["model"] == "hy3"
    assert requests[0]["chat_template_kwargs"] == {"reasoning_effort": "high"}
