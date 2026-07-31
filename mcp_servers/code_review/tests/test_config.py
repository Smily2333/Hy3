import pytest

from hy3_code_review_mcp.config import ConfigurationError, Hy3Settings


def test_settings_load_valid_environment() -> None:
    settings = Hy3Settings.from_env(
        {
            "HY3_API_KEY": "test-key",
            "HY3_BASE_URL": "https://example.test/v1/",
            "HY3_MODEL": "hy3-test",
            "HY3_TIMEOUT_SECONDS": "30",
            "HY3_MAX_RETRIES": "1",
            "HY3_REASONING_EFFORT": "low",
            "HY3_MAX_INPUT_CHARS": "1000",
            "HY3_MAX_OUTPUT_TOKENS": "500",
        }
    )

    assert settings.api_key == "test-key"
    assert settings.base_url == "https://example.test/v1"
    assert settings.model == "hy3-test"
    assert settings.timeout_seconds == 30
    assert settings.max_retries == 1
    assert settings.reasoning_effort == "low"
    assert settings.max_input_chars == 1000
    assert settings.max_output_tokens == 500


def test_settings_require_api_key_for_tool_calls() -> None:
    with pytest.raises(ConfigurationError, match="HY3_API_KEY"):
        Hy3Settings.from_env({})


def test_settings_can_load_without_api_key_for_discovery() -> None:
    settings = Hy3Settings.from_env({}, require_api_key=False)
    assert settings.api_key == ""


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("HY3_TIMEOUT_SECONDS", "0"),
        ("HY3_MAX_RETRIES", "-1"),
        ("HY3_REASONING_EFFORT", "medium"),
        ("HY3_BASE_URL", "not-a-url"),
    ],
)
def test_settings_reject_invalid_values(name: str, value: str) -> None:
    with pytest.raises(ConfigurationError):
        Hy3Settings.from_env({"HY3_API_KEY": "test", name: value})
