"""Business logic shared by the MCP tool handlers."""

from __future__ import annotations

from typing import Protocol

from hy3_code_review_mcp.config import Hy3Settings
from hy3_code_review_mcp.parsing import parse_model
from hy3_code_review_mcp.prompts import (
    EXPLAIN_SYSTEM_PROMPT,
    REVIEW_SYSTEM_PROMPT,
    TEST_PLAN_SYSTEM_PROMPT,
    user_payload,
)
from hy3_code_review_mcp.schemas import (
    ChangeExplanation,
    ReviewResult,
    Severity,
    TestPlan,
)

SEVERITY_RANK: dict[Severity, int] = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}
MAX_CONTEXT_CHARS = 8_000
MAX_SHORT_OPTION_CHARS = 200


class InputValidationError(ValueError):
    """Raised when MCP tool input is missing or exceeds a safe bound."""


class CompletionProvider(Protocol):
    """Minimal completion interface used by the service."""

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str: ...


def _required_diff(diff: str, max_chars: int) -> str:
    value = diff.strip()
    if not value:
        raise InputValidationError("diff must not be empty")
    if len(value) > max_chars:
        raise InputValidationError(f"diff exceeds HY3_MAX_INPUT_CHARS ({max_chars} characters)")
    return value


def _bounded(value: str, name: str, max_chars: int) -> str:
    normalized = value.strip()
    if len(normalized) > max_chars:
        raise InputValidationError(f"{name} must not exceed {max_chars} characters")
    return normalized


class CodeReviewService:
    """Validate tool inputs, call Hy3, and enforce output schemas."""

    def __init__(
        self,
        *,
        settings: Hy3Settings,
        client: CompletionProvider,
    ) -> None:
        self.settings = settings
        self.client = client

    async def review_diff(
        self,
        *,
        diff: str,
        focus: str,
        project_context: str,
        severity_threshold: Severity,
    ) -> ReviewResult:
        """Review one diff and filter findings below the requested severity."""
        validated_diff = _required_diff(diff, self.settings.max_input_chars)
        validated_focus = (
            _bounded(focus, "focus", MAX_SHORT_OPTION_CHARS)
            or "correctness, security, and maintainability"
        )
        validated_context = _bounded(project_context, "project_context", MAX_CONTEXT_CHARS)

        text = await self.client.complete(
            system_prompt=REVIEW_SYSTEM_PROMPT,
            user_prompt=user_payload(
                diff=validated_diff,
                focus=validated_focus,
                project_context=validated_context,
                severity_threshold=severity_threshold,
            ),
        )
        result = parse_model(text, ReviewResult)
        minimum_rank = SEVERITY_RANK[severity_threshold]
        original_count = len(result.findings)
        filtered_findings = [
            finding
            for finding in result.findings
            if SEVERITY_RANK[finding.severity] >= minimum_rank
        ]
        if len(filtered_findings) != original_count:
            result.summary = (
                f"Returned {len(filtered_findings)} finding(s) at or above "
                f"{severity_threshold}; {original_count - len(filtered_findings)} "
                "lower-severity finding(s) omitted."
            )
        result.findings = filtered_findings
        return result

    async def explain_changes(
        self,
        *,
        diff: str,
        audience: str,
        project_context: str,
        include_risks: bool,
    ) -> ChangeExplanation:
        """Explain the purpose and impact of one diff."""
        validated_diff = _required_diff(diff, self.settings.max_input_chars)
        validated_audience = _bounded(audience, "audience", MAX_SHORT_OPTION_CHARS) or "maintainer"
        validated_context = _bounded(project_context, "project_context", MAX_CONTEXT_CHARS)

        text = await self.client.complete(
            system_prompt=EXPLAIN_SYSTEM_PROMPT,
            user_prompt=user_payload(
                diff=validated_diff,
                audience=validated_audience,
                project_context=validated_context,
                include_risks=include_risks,
            ),
        )
        result = parse_model(text, ChangeExplanation)
        if not include_risks:
            result.risks = []
        return result

    async def generate_test_plan(
        self,
        *,
        diff: str,
        test_framework: str,
        existing_tests: str,
        project_context: str,
    ) -> TestPlan:
        """Generate a prioritized test plan for one diff."""
        validated_diff = _required_diff(diff, self.settings.max_input_chars)
        validated_framework = (
            _bounded(test_framework, "test_framework", MAX_SHORT_OPTION_CHARS) or "unspecified"
        )
        validated_existing_tests = _bounded(existing_tests, "existing_tests", MAX_CONTEXT_CHARS)
        validated_context = _bounded(project_context, "project_context", MAX_CONTEXT_CHARS)

        text = await self.client.complete(
            system_prompt=TEST_PLAN_SYSTEM_PROMPT,
            user_prompt=user_payload(
                diff=validated_diff,
                test_framework=validated_framework,
                existing_tests=validated_existing_tests,
                project_context=validated_context,
            ),
        )
        return parse_model(text, TestPlan)
