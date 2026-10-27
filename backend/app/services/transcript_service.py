"""Reads an uploaded transcript: rules first, AI only when the rules clearly struggled."""

import logging

from fastapi.concurrency import run_in_threadpool

from app.constants import MIN_GRADED_SHARE, MIN_RULE_READ_COURSES
from app.errors import AIServiceError
from app.models.course import StudyPlan
from app.models.student import ParsedTranscript, TranscriptCourse, TranscriptReader
from app.services.ai_transcript_reader import AITranscriptReader
from app.services.pdf_parser import extract_text_lines
from app.services.transcript_analyzer import analyze_transcript

logger = logging.getLogger(__name__)


def needs_ai_reading(result: ParsedTranscript) -> bool:
    """True when the rule-based result looks like a layout the rules did not understand."""
    if len(result.courses) < MIN_RULE_READ_COURSES:
        return True
    graded = sum(1 for course in result.courses if course.grade is not None)
    return graded / len(result.courses) < MIN_GRADED_SHARE


class TranscriptService:
    """Turns PDF bytes into the plan courses a student has taken."""

    def __init__(self, ai_reader: AITranscriptReader | None) -> None:
        self._ai_reader = ai_reader

    async def parse(self, data: bytes, plan: StudyPlan) -> ParsedTranscript:
        """Read ``data`` against ``plan``.

        The AI reader is used only if the rule-based result looks wrong, and its answer is
        kept only if it recognises more graded courses than the rules did.
        """
        lines = await run_in_threadpool(extract_text_lines, data)
        return await self.parse_lines(lines, plan)

    async def parse_lines(self, lines: list[str], plan: StudyPlan) -> ParsedTranscript:
        """Same as :meth:`parse` for text that has already been extracted."""
        result = analyze_transcript(lines, plan)
        if self._ai_reader is None or not needs_ai_reading(result):
            return result

        try:
            courses = await self._ai_reader.read(lines, plan)
        except AIServiceError as error:
            logger.warning("AI transcript reading failed (%s); keeping the rule-based result", error)
            return result

        if _graded_count(courses) > _graded_count(result.courses):
            return result.model_copy(update={"courses": courses, "reader": TranscriptReader.AI})
        return result


def _graded_count(courses: list[TranscriptCourse]) -> int:
    return sum(1 for course in courses if course.grade is not None)
