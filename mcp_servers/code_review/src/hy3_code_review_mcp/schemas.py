"""Structured output contracts for the planned code-review tools."""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

Severity: TypeAlias = Literal["critical", "high", "medium", "low"]


class Finding(BaseModel):
    """One actionable code-review finding."""

    severity: Severity
    location: str = Field(min_length=1)
    title: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    suggestion: str = Field(min_length=1)


class ReviewResult(BaseModel):
    """Output returned by the code-review tool."""

    summary: str = Field(min_length=1)
    findings: list[Finding]


class ChangeExplanation(BaseModel):
    """Output returned by the change-explanation tool."""

    purpose: str = Field(min_length=1)
    behavior_changes: list[str]
    affected_areas: list[str]
    risks: list[str]
    reviewer_focus: list[str]


class TestCase(BaseModel):
    """One proposed test case."""

    priority: Literal["high", "medium", "low"]
    category: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    expected_result: str = Field(min_length=1)


class TestPlan(BaseModel):
    """Output returned by the test-plan tool."""

    summary: str = Field(min_length=1)
    cases: list[TestCase]
