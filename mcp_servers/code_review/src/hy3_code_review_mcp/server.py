"""MCP server entry point for Hy3 Code Review MCP."""

from mcp.server.fastmcp import FastMCP

from hy3_code_review_mcp.config import Hy3Settings
from hy3_code_review_mcp.hy3_client import Hy3Client
from hy3_code_review_mcp.schemas import (
    ChangeExplanation,
    ReviewResult,
    Severity,
    TestPlan,
)
from hy3_code_review_mcp.service import CodeReviewService

mcp = FastMCP(
    "hy3-code-review-mcp",
    instructions=(
        "A local MCP server that uses Hy3 to review diffs, explain changes, "
        "and generate test plans."
    ),
)

_service: CodeReviewService | None = None


def _get_service() -> CodeReviewService:
    global _service
    if _service is None:
        settings = Hy3Settings.from_env()
        _service = CodeReviewService(settings=settings, client=Hy3Client(settings))
    return _service


@mcp.tool()
async def review_diff(
    diff: str,
    focus: str = "correctness, security, and maintainability",
    project_context: str = "",
    severity_threshold: Severity = "low",
) -> ReviewResult:
    """Review a unified diff with Hy3 and return actionable findings.

    Args:
        diff: Unified diff text to review.
        focus: Review priorities such as correctness, security, or performance.
        project_context: Optional language, framework, and project constraints.
        severity_threshold: Lowest severity to include in the result.
    """
    return await _get_service().review_diff(
        diff=diff,
        focus=focus,
        project_context=project_context,
        severity_threshold=severity_threshold,
    )


@mcp.tool()
async def explain_changes(
    diff: str,
    audience: str = "maintainer",
    project_context: str = "",
    include_risks: bool = True,
) -> ChangeExplanation:
    """Explain the purpose, behavior, impact, and risks of a unified diff.

    Args:
        diff: Unified diff text to explain.
        audience: Intended reader, for example beginner, maintainer, or reviewer.
        project_context: Optional language, framework, and project constraints.
        include_risks: Whether the response should include rollout and regression risks.
    """
    return await _get_service().explain_changes(
        diff=diff,
        audience=audience,
        project_context=project_context,
        include_risks=include_risks,
    )


@mcp.tool()
async def generate_test_plan(
    diff: str,
    test_framework: str = "unspecified",
    existing_tests: str = "",
    project_context: str = "",
) -> TestPlan:
    """Generate a prioritized test plan for a unified diff with Hy3.

    Args:
        diff: Unified diff text that the tests must cover.
        test_framework: Preferred framework, such as pytest, Jest, or JUnit.
        existing_tests: Optional summary or excerpts of relevant existing tests.
        project_context: Optional language, framework, and project constraints.
    """
    return await _get_service().generate_test_plan(
        diff=diff,
        test_framework=test_framework,
        existing_tests=existing_tests,
        project_context=project_context,
    )


def main() -> None:
    """Run the MCP server over the local stdio transport."""
    mcp.run(transport="stdio")
