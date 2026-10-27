import json
from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.errors import AIServiceError
from app.services.gemini_client import GeminiJsonClient

pytestmark = pytest.mark.anyio


class Answer(BaseModel):
    value: int


class FakeModels:
    def __init__(self, text: str | None = None, error: Exception | None = None) -> None:
        self.text, self.error, self.calls = text, error, []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.text)


def client_with(models: FakeModels) -> GeminiJsonClient:
    client = GeminiJsonClient(api_key="test-key", model="test-model", timeout_seconds=1)
    client._client = SimpleNamespace(aio=SimpleNamespace(models=models))
    return client


async def test_returns_the_answer_parsed_into_the_schema():
    models = FakeModels(json.dumps({"value": 7}))

    answer = await client_with(models).generate(system_prompt="p", contents="c", schema=Answer)

    assert answer == Answer(value=7)
    assert models.calls[0]["model"] == "test-model"
    assert models.calls[0]["config"].response_schema is Answer


@pytest.mark.parametrize("text", [None, "", "not json", json.dumps({"value": "seven"})])
async def test_unusable_responses_raise_ai_service_error(text):
    with pytest.raises(AIServiceError):
        await client_with(FakeModels(text)).generate(system_prompt="p", contents="c", schema=Answer)


async def test_api_failures_raise_ai_service_error():
    error = genai_errors.APIError(500, {"error": {"message": "boom"}})

    with pytest.raises(AIServiceError):
        await client_with(FakeModels(error=error)).generate(system_prompt="p", contents="c", schema=Answer)
