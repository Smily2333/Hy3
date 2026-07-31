"""Environment-backed configuration for the Hy3 API."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://tokenhub.tencentmaas.com/v1"
DEFAULT_MODEL = "hy3"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_INPUT_CHARS = 60_000
DEFAULT_MAX_OUTPUT_TOKENS = 8_000
VALID_REASONING_EFFORTS = frozenset({"no_think", "low", "high"})


class ConfigurationError(ValueError):
    """Raised when required configuration is missing or invalid."""


def _positive_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero")
    return value


def _non_negative_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = env.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if value < 0:
        raise ConfigurationError(f"{name} must be zero or greater")
    return value


@dataclass(frozen=True, slots=True)
class Hy3Settings:
    """Validated settings used by the Hy3 API client."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    reasoning_effort: str = "high"
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        require_api_key: bool = True,
    ) -> Hy3Settings:
        """Load settings from environment variables and validate them."""
        values = os.environ if env is None else env

        api_key = values.get("HY3_API_KEY", "").strip()
        if require_api_key and not api_key:
            raise ConfigurationError("HY3_API_KEY is required when invoking a Hy3-backed tool")

        base_url = values.get("HY3_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
        if not base_url:
            raise ConfigurationError("HY3_BASE_URL must not be empty")
        if not base_url.startswith(("http://", "https://")):
            raise ConfigurationError("HY3_BASE_URL must start with http:// or https://")

        model = values.get("HY3_MODEL", DEFAULT_MODEL).strip()
        if not model:
            raise ConfigurationError("HY3_MODEL must not be empty")

        reasoning_effort = values.get("HY3_REASONING_EFFORT", "high").strip()
        if reasoning_effort not in VALID_REASONING_EFFORTS:
            allowed = ", ".join(sorted(VALID_REASONING_EFFORTS))
            raise ConfigurationError(f"HY3_REASONING_EFFORT must be one of: {allowed}")

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=_positive_int(values, "HY3_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
            max_retries=_non_negative_int(values, "HY3_MAX_RETRIES", DEFAULT_MAX_RETRIES),
            reasoning_effort=reasoning_effort,
            max_input_chars=_positive_int(values, "HY3_MAX_INPUT_CHARS", DEFAULT_MAX_INPUT_CHARS),
            max_output_tokens=_positive_int(
                values, "HY3_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS
            ),
        )
