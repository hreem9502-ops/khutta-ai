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
from app.services.transcript_analyzer import course_from_grade, merge_attempts, normalize_token

SYSTEM_PROMPT = """\
You read course results and cumulative GPA out of a university or technical-college transcript.

Rules:
- Return one entry per course row you find. A course may appear more than once \
(for example a failed attempt and a retake); return every attempt.
- "code": the course code exactly as it appears in "known_codes" (refer to "plan_courses" \
for each code's Arabic and English title).
- Match a row to a course in "plan_courses" ONLY when either its course code matches \
(including reversed RTL prefixes such as "111 اكبش" -> "شبكا 111") OR no course code is \
present on the row and the course title clearly matches that exact plan course. Never \
translate or map a course code from a different numbering/prefix system (for example, \
never map "رياض 101" or "حاسب 101" to "MATH 101" or "CS 101").
- "grade": the grade symbol or word (for example "A+", "A", "B+", "C", "D", "F", "IP", \
"ممتاز", "جيد جدا", "جيد", "مقبول", "راسب"), or null when the row has no grade yet.
- "gpa": the student's cumulative GPA as a number if explicitly shown, otherwise null.
- The text may be Arabic, English or mixed, and Arabic words/letters may appear in \
visual reversed order.
- Never include personal data. Ignore headers, totals and anything that is not a course row.
"""

_PERSONAL_LABELS = re.compile(
    r"name|student|\bid\b|national|passport|phone|mobile|e-?mail|"
    r"الاسم|اسم|رقم|هوية|السجل المدني|جوال|بريد|"
    r"مسالاا|مسا|مقر|ةيوه|يندمل|لاوج|ديرب",
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
    gpa: float | None = None


def _sanitize_line(line: str) -> str:
    return _EMAIL.sub("#", _LONG_NUMBER.sub("#", line))


def select_course_lines(lines: Iterable[str], plan: StudyPlan | None = None) -> list[str]:
    """Keep only lines that may be course rows (or GPA lines when ``plan`` is given), with PII removed.

    A course row carries a 3-4 digit course number (or, when ``plan`` is supplied, a known
    course title); lines with personal labels are dropped entirely, and long numbers (IDs,
    phone numbers) and email addresses are masked.
    """
    title_tokens: set[str] = set()
    if plan is not None:
        for course in plan.courses:
            for title in (course.name.ar, course.name.en, course.name.ar[::-1]):
                cleaned = normalize_token(title)
                if len(cleaned) >= 5:
                    title_tokens.add(cleaned)

    selected: list[str] = []
    for line in lines:
        if _PERSONAL_LABELS.search(line):
            continue
        has_short_number = bool(_SHORT_NUMBER.search(line))
        has_known_title = False
        if not has_short_number and title_tokens:
            norm_line = normalize_token(line)
            has_known_title = any(title in norm_line for title in title_tokens) or (
                "GPA" in norm_line or "المعدل" in line or "لدعملا" in line
            )
        if has_short_number or has_known_title:
            selected.append(_sanitize_line(line))
    return selected[:MAX_AI_TRANSCRIPT_LINES]


class AITranscriptReader:
    """Asks the model for the course rows in a transcript."""

    def __init__(self, client: JsonModelClient) -> None:
        self._client = client

    async def read(self, lines: Iterable[str], plan: StudyPlan) -> list[TranscriptCourse]:
        """Return the plan courses the model found, merged per course."""
        courses, _ = await self.read_with_gpa(lines, plan)
        return courses

    async def read_with_gpa(
        self, lines: Iterable[str], plan: StudyPlan
    ) -> tuple[list[TranscriptCourse], float | None]:
        """Return ``(courses, gpa)`` read by the model from extracted transcript ``lines``."""
        course_lines = select_course_lines(lines, plan)
        if not course_lines:
            return [], None

        payload = self._plan_payload(plan) | {"lines": course_lines}
        output = await self._client.generate(
            system_prompt=SYSTEM_PROMPT,
            contents=json.dumps(payload, ensure_ascii=False),
            schema=_Rows,
        )
        return self._filter_output(output, plan)

    async def read_pdf(self, pdf_bytes: bytes, plan: StudyPlan) -> tuple[list[TranscriptCourse], float | None]:
        """Read a scanned or image-based PDF directly with Gemini Vision when supported."""
        generate_from_pdf = getattr(self._client, "generate_from_pdf", None)
        if not callable(generate_from_pdf):
            return [], None
        prompt = json.dumps(self._plan_payload(plan), ensure_ascii=False)
        output = await generate_from_pdf(
            system_prompt=SYSTEM_PROMPT,
            pdf_bytes=pdf_bytes,
            prompt=f"Read the courses and cumulative GPA from this transcript PDF using this plan:\n{prompt}",
            schema=_Rows,
        )
        return self._filter_output(output, plan)

    @staticmethod
    def _plan_payload(plan: StudyPlan) -> dict:
        return {
            "known_codes": [course.code for course in plan.courses],
            "plan_courses": [
                {"code": course.code, "ar": course.name.ar, "en": course.name.en}
                for course in plan.courses
            ],
            "gpa_scale": plan.rules.gpa_scale,
        }

    @staticmethod
    def _filter_output(output: _Rows, plan: StudyPlan) -> tuple[list[TranscriptCourse], float | None]:
        attempts = []
        for row in output.courses:
            code = normalize_course_code(row.code)
            if code in plan.by_code:
                attempts.append(course_from_grade(code, row.grade))
        gpa = output.gpa if (output.gpa is not None and 0 < output.gpa <= plan.rules.gpa_scale) else None
        return merge_attempts(attempts, plan), gpa
