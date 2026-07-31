"""Parsing helpers for model-generated structured output."""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

ResultModel = TypeVar("ResultModel", bound=BaseModel)


class Hy3ResponseError(ValueError):
    """Raised when a Hy3 response cannot be parsed into the expected schema."""


def _json_object(text: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise Hy3ResponseError("Hy3 response did not contain a valid JSON object")


def parse_model(text: str, model: type[ResultModel]) -> ResultModel:
    """Extract the first JSON object from model text and validate it."""
    try:
        return model.model_validate(_json_object(text))
    except ValidationError as exc:
        raise Hy3ResponseError(f"Hy3 response did not match {model.__name__}") from exc
