"""Test doubles for the AI client."""

from typing import Any


class FakeJsonClient:
    """Stands in for ``GeminiJsonClient``: returns a canned answer or raises."""

    def __init__(self, answer: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self.answer = answer
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def generate(self, *, system_prompt: str, contents: str, schema):
        self.calls.append({"system_prompt": system_prompt, "contents": contents})
        if self.error:
            raise self.error
        return schema.model_validate(self.answer)
