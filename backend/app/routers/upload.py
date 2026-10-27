"""Transcript upload endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import Settings, get_settings
from app.dependencies import get_plan_repository, get_transcript_service
from app.uploads import read_upload
from app.models.student import ParsedTranscript
from app.services.plan_repository import PlanRepository
from app.services.transcript_service import TranscriptService

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/parse", response_model=ParsedTranscript)
async def parse_transcript(
    file: Annotated[UploadFile, File(description="Transcript PDF")],
    department: Annotated[str, Form()],
    plans: Annotated[PlanRepository, Depends(get_plan_repository)],
    transcripts: Annotated[TranscriptService, Depends(get_transcript_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ParsedTranscript:
    """Read a transcript PDF and report which plan courses it shows.

    The file is processed in memory and never stored. If the rule-based reader cannot
    follow the layout and AI is configured, course rows (with personal data removed) are
    read by the model instead; ``reader`` in the response says which one was used.
    """
    plan = plans.get(department)
    data = await read_upload(file, settings.max_upload_bytes)
    return await transcripts.parse(data, plan)
