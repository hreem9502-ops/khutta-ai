"""AI fallback for transcripts whose layout the rule-based reader cannot follow.

Only lines that look like course rows are sent: lines carrying personal labels (name, ID,
phone, email) are dropped and long digit runs are masked. The model's answer is filtered
through the study plan, so it can only report courses that exist in the plan, and the
student still confirms every course on the review screen.
"""

import json
import re
from collections.abc import Iterable

from pydantic import BaseModel

from app.constants import MAX_AI_TRANSCRIPT_LINES
from app.models.common import normalize_course_code
from app.models.course import StudyPlan
from app.models.student import TranscriptCourse
from app.services.gemini_client import JsonModelClient
from app.services.transcript_analyzer import course_from_grade, merge_attempts

SYSTEM_PROMPT = """\
You read course results out of text extracted from a university transcript PDF.

Rules:
- Return one entry per course row you find. A course may appear more than once \
(for example a failed attempt and a retake); return every attempt.
- "code": the course code exactly as it appears in "known_codes". Skip rows whose \
course is not in "known_codes".
- "grade": the grade exactly as written (for example "A", "B+", "F", "IP", or an Arabic \
word such as "ممتاز" or "راسب"), or null when the row has no grade yet.
- The text may be Arabic, English or mixed, and Arabic text may appear in reversed order.
- Ignore headers, totals, GPA lines and anything that is not a course row.
"""

_PERSONAL_LABELS = re.compile(
    r"name|student|\bid\b|national|passport|phone|mobile|e-?mail|"
    r"الاسم|اسم|رقم|هوية|السجل المدني|جوال|بريد",
    re.IGNORECASE,
)
_SHORT_NUMBER = re.compile(r"(?<!\d)\d{3,4}(?!\d)")
_LONG_NUMBER = re.compile(r"\d{6,}")
_EMAIL = re.compile(r"\S+@\S+")


class _Row(BaseModel):
    code: str
    grade: str | None


class _Rows(BaseModel):
    """Response schema enforced on the model."""

    courses: list[_Row]


def select_course_lines(lines: Iterable[str]) -> list[str]:
    """Keep only lines that may be course rows, with personal data removed.

    A course row carries a 3-4 digit course number; lines with personal labels are dropped
    entirely, and long numbers (IDs, phone numbers) and email addresses are masked.
    """
    selected = [
        _EMAIL.sub("#", _LONG_NUMBER.sub("#", line))
        for line in lines
        if _SHORT_NUMBER.search(line) and not _PERSONAL_LABELS.search(line)
    ]
    return selected[:MAX_AI_TRANSCRIPT_LINES]


class AITranscriptReader:
    """Asks the model for the course rows in a transcript."""

    def __init__(self, client: JsonModelClient) -> None:
        self._client = client

    async def read(self, lines: Iterable[str], plan: StudyPlan) -> list[TranscriptCourse]:
        """Return the plan courses the model found, merged per course.

        Raises:
            AIServiceError: the model could not be reached or answered unusably.
        """
        course_lines = select_course_lines(lines)
        if not course_lines:
            return []

        payload = {"known_codes": [course.code for course in plan.courses], "lines": course_lines}
        output = await self._client.generate(
            system_prompt=SYSTEM_PROMPT,
            contents=json.dumps(payload, ensure_ascii=False),
            schema=_Rows,
        )

        attempts = []
        for row in output.courses:
            code = normalize_course_code(row.code)
            if code in plan.by_code:
                attempts.append(course_from_grade(code, row.grade))
        return merge_attempts(attempts, plan)
