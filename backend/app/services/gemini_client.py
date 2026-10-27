"""Thin wrapper around the Gemini SDK for calls that must return schema-validated JSON."""

import asyncio
from typing import Protocol, TypeVar

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.errors import AIServiceError

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class JsonModelClient(Protocol):
    """Anything that can answer a prompt with an instance of ``schema``."""

    async def generate(self, *, system_prompt: str, contents: str, schema: type[SchemaT]) -> SchemaT: ...


class GeminiJsonClient:
    """Calls Gemini with a response schema and validates the answer."""

    def __init__(
        self,
        api_key: str | list[str],
        model: str,
        timeout_seconds: float,
        temperature: float = 0.2,
    ) -> None:
        keys = [api_key] if isinstance(api_key, str) else list(api_key)
        self._keys = [key.strip() for key in keys if key.strip()]
        self._key_index = 0
        self._client = genai.Client(api_key=self._keys[0])
        self._model = model
        self._timeout = timeout_seconds
        self._temperature = temperature

    def _switch_to_next_key(self) -> bool:
        """Move to the next API key; return ``False`` when none is left."""
        if self._key_index + 1 >= len(self._keys):
            return False
        self._key_index += 1
        self._client = genai.Client(api_key=self._keys[self._key_index])
        return True

    async def generate(self, *, system_prompt: str, contents: str, schema: type[SchemaT]) -> SchemaT:
        """Return the model's answer parsed into ``schema``.

        When a key's quota is exhausted the client switches to the next configured key and
        retries, and keeps using that key for later calls.

        Raises:
            AIServiceError: the call failed, timed out, or returned an unusable response.
        """
        return await self._call(system_prompt=system_prompt, contents=contents, schema=schema)

    async def generate_from_pdf(
        self, *, system_prompt: str, pdf_bytes: bytes, prompt: str, schema: type[SchemaT]
    ) -> SchemaT:
        """Read a PDF document directly (including scanned/image PDFs) into ``schema``."""
        contents = [types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"), prompt]
        return await self._call(system_prompt=system_prompt, contents=contents, schema=schema)

    async def _call(self, *, system_prompt: str, contents: object, schema: type[SchemaT]) -> SchemaT:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=self._temperature,
        )
        while True:
            try:
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(model=self._model, contents=contents, config=config),
                    timeout=self._timeout,
                )
                if not response.text:
                    raise AIServiceError("Model returned an empty response")
                return schema.model_validate_json(response.text)
            except genai_errors.APIError as error:
                if _is_quota_error(error) and self._switch_to_next_key():
                    continue
                raise AIServiceError(f"{type(error).__name__}: {error}") from error
            except (TimeoutError, ValidationError) as error:
                raise AIServiceError(f"{type(error).__name__}: {error}") from error


def _is_quota_error(error: genai_errors.APIError) -> bool:
    """True when the error means the key's quota or rate limit is used up."""
    return error.code == 429 or "RESOURCE_EXHAUSTED" in str(error)
