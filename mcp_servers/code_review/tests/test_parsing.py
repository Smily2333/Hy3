import pytest

from hy3_code_review_mcp.parsing import Hy3ResponseError, parse_model
from hy3_code_review_mcp.schemas import ReviewResult


def test_parse_model_accepts_fenced_json_with_surrounding_text() -> None:
    text = """
Result:
```json
{"summary":"Looks safe.","findings":[]}
```
"""

    result = parse_model(text, ReviewResult)

    assert result.summary == "Looks safe."
    assert result.findings == []


def test_parse_model_rejects_invalid_schema() -> None:
    with pytest.raises(Hy3ResponseError, match="ReviewResult"):
        parse_model('{"summary":"","findings":[]}', ReviewResult)


def test_parse_model_rejects_missing_json() -> None:
    with pytest.raises(Hy3ResponseError, match="valid JSON"):
        parse_model("No structured result was returned.", ReviewResult)
