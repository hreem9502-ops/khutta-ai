"""Shared handling of uploaded files."""

from fastapi import UploadFile

from app.errors import FileTooLargeError


async def read_upload(file: UploadFile, limit: int) -> bytes:
    """Read ``file`` into memory, refusing anything larger than ``limit`` bytes."""
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise FileTooLargeError(f"Limit is {limit} bytes")
    return data
