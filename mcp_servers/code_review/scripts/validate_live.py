"""Run live Hy3 acceptance checks through the MCP stdio transport.

This script reads local settings from ``.env`` without printing the API key,
starts the packaged MCP server, and invokes all three tools with the repository
demo diffs.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parents[1]
EXPECTED_TOOLS = {
    "review_diff",
    "explain_changes",
    "generate_test_plan",
}


def load_local_env() -> dict[str, str]:
    """Load the simple KEY=VALUE entries used by this project."""
    env_path = PROJECT_DIR / ".env"
    if not env_path.is_file():
        raise RuntimeError(f"Missing local environment file: {env_path}")

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip()

    if not values.get("HY3_API_KEY"):
        raise RuntimeError("HY3_API_KEY is missing or empty in .env")
    return values


def require_success(name: str, result: Any) -> dict[str, Any]:
    """Return structured content or raise a useful acceptance-test error."""
    if result.isError:
        message = result.content[0].text if result.content else "unknown MCP error"
        raise RuntimeError(f"{name} failed: {message}")
    if not result.structuredContent:
        raise RuntimeError(f"{name} returned no structured content")
    return result.structuredContent


async def validate() -> dict[str, Any]:
    """Invoke every tool through a real MCP subprocess and summarize evidence."""
    child_env = os.environ.copy()
    child_env.update(load_local_env())
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "hy3_code_review_mcp"],
        cwd=PROJECT_DIR,
        env=child_env,
    )

    bug_diff = (PROJECT_DIR / "examples" / "sample_bug.diff").read_text(encoding="utf-8")
    feature_diff = (PROJECT_DIR / "examples" / "sample_feature.diff").read_text(encoding="utf-8")

    async with (
        stdio_client(server) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        listed = {tool.name for tool in (await session.list_tools()).tools}
        if listed != EXPECTED_TOOLS:
            raise RuntimeError(f"Unexpected tool set: {sorted(listed)}")

        review = require_success(
            "review_diff",
            await session.call_tool(
                "review_diff",
                {
                    "diff": bug_diff,
                    "focus": "correctness and runtime safety",
                    "project_context": "Python service",
                    "severity_threshold": "medium",
                },
            ),
        )
        if not review["findings"]:
            raise RuntimeError("review_diff did not identify the demonstrated null defect")

        explanation = require_success(
            "explain_changes",
            await session.call_tool(
                "explain_changes",
                {
                    "diff": bug_diff,
                    "audience": "maintainer",
                    "project_context": "Python service",
                    "include_risks": True,
                },
            ),
        )
        if not explanation["behavior_changes"]:
            raise RuntimeError("explain_changes returned no behavior changes")

        test_plan = require_success(
            "generate_test_plan",
            await session.call_tool(
                "generate_test_plan",
                {
                    "diff": feature_diff,
                    "test_framework": "pytest",
                    "project_context": "Python service with one-based pagination",
                },
            ),
        )
        if not test_plan["cases"]:
            raise RuntimeError("generate_test_plan returned no test cases")

    return {
        "transport": "stdio",
        "tools": sorted(listed),
        "review_diff": {
            "finding_count": len(review["findings"]),
            "findings": [
                {
                    "severity": finding["severity"],
                    "location": finding["location"],
                    "title": finding["title"],
                }
                for finding in review["findings"]
            ],
        },
        "explain_changes": {
            "behavior_change_count": len(explanation["behavior_changes"]),
            "risk_count": len(explanation["risks"]),
            "purpose": explanation["purpose"],
        },
        "generate_test_plan": {
            "case_count": len(test_plan["cases"]),
            "high_priority_count": sum(case["priority"] == "high" for case in test_plan["cases"]),
            "scenarios": [case["scenario"] for case in test_plan["cases"]],
        },
    }


def main() -> None:
    """Run the asynchronous live validation."""
    print(json.dumps(asyncio.run(validate()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
