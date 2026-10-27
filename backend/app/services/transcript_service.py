"""Reads an uploaded transcript: rules first, AI only when the rules clearly struggled."""

import logging

from fastapi.concurrency import run_in_threadpool

from app.constants import MIN_GRADED_SHARE, MIN_RULE_READ_COURSES
from app.errors import AIServiceError, UnreadableTranscriptError
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

    async def parse(self, data: bytes, plan: StudyPlan, fallback_plans: list[StudyPlan] | None = None) -> ParsedTranscript:
        """Read ``data`` against ``plan`` (and ``fallback_plans`` if ``plan`` clearly does not match).

        Rules are checked across ``plan`` (and ``fallback_plans`` when ``plan`` has no rule
        matches) before calling AI, so uploading a transcript under the wrong department
        switches cleanly to the matching department without hallucinating cross-plan mappings.
        If the PDF is a scanned image with no text layer and AI Vision is configured, the PDF
        is read directly by Gemini Vision.
        """
        candidates = [plan, *(p for p in (fallback_plans or []) if p.code != plan.code)]
        try:
            lines = await run_in_threadpool(extract_text_lines, data)
        except UnreadableTranscriptError:
            if self._ai_reader is None:
                raise
            return await self._parse_scanned_pdf(data, candidates)

        # 1. Fast rule-based check on the chosen plan first, then fallback plans if rules struggled.
        best_plan = plan
        best_rule = analyze_transcript(lines, plan)
        if needs_ai_reading(best_rule) and len(candidates) > 1:
            for other in candidates[1:]:
                candidate_rule = analyze_transcript(lines, other)
                if (_graded_count(candidate_rule.courses), len(candidate_rule.courses)) > (
                    _graded_count(best_rule.courses),
                    len(best_rule.courses),
                ):
                    best_plan = other
                    best_rule = candidate_rule

        if self._ai_reader is None or not needs_ai_reading(best_rule):
            return best_rule

        # 2. AI fallback on the best candidate plan (and other plans if still empty).
        result = await self._ai_read_lines(lines, best_plan, best_rule)
        if not result.courses and len(candidates) > 1:
            for other in candidates:
                if other.code == best_plan.code:
                    continue
                other_rule = analyze_transcript(lines, other)
                other_result = await self._ai_read_lines(lines, other, other_rule)
                if len(other_result.courses) > len(result.courses):
                    result = other_result
        return result

    async def parse_lines(self, lines: list[str], plan: StudyPlan) -> ParsedTranscript:
        """Same as :meth:`parse` for text that has already been extracted."""
        result = analyze_transcript(lines, plan)
        if self._ai_reader is None or not needs_ai_reading(result):
            return result
        return await self._ai_read_lines(lines, plan, result)

    async def _ai_read_lines(
        self, lines: list[str], plan: StudyPlan, rule_result: ParsedTranscript
    ) -> ParsedTranscript:
        assert self._ai_reader is not None
        try:
            courses, ai_gpa = await self._ai_reader.read_with_gpa(lines, plan)
        except AIServiceError as error:
            logger.warning("AI transcript reading failed (%s); keeping the rule-based result", error)
            return rule_result

        if _graded_count(courses) > _graded_count(rule_result.courses) or (
            not rule_result.courses and courses
        ):
            return rule_result.model_copy(
                update={
                    "courses": courses,
                    "gpa": rule_result.gpa if rule_result.gpa is not None else ai_gpa,
                    "reader": TranscriptReader.AI,
                }
            )
        return rule_result

    async def _parse_scanned_pdf(self, data: bytes, candidates: list[StudyPlan]) -> ParsedTranscript:
        assert self._ai_reader is not None
        for candidate in candidates:
            try:
                courses, gpa = await self._ai_reader.read_pdf(data, candidate)
            except AIServiceError as error:
                logger.warning("AI scanned-PDF reading failed (%s)", error)
                break
            if courses:
                return ParsedTranscript(
                    department=candidate.code,
                    courses=courses,
                    gpa=gpa,
                    reader=TranscriptReader.AI,
                )
        raise UnreadableTranscriptError("PDF contains no extractable text")


def _graded_count(courses: list[TranscriptCourse]) -> int:
    return sum(1 for course in courses if course.grade is not None)
