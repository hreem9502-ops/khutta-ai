"""Gemini-backed advisor: picks and explains a schedule from the eligible courses.

The model never sees raw transcript text, names or student IDs. It receives only course
codes, grades and the already-filtered list of eligible courses, and its answer is
re-validated by the recommender, so a bad response cannot register an ineligible course.
"""

import json

from pydantic import BaseModel

from app.models.common import LocalizedText
from app.models.suggestion import Priority, RecommendationSource
from app.services.advisor_types import AdvisorContext, Choice, Selection
from app.services.gemini_client import JsonModelClient

SYSTEM_PROMPT = """\
You are an expert academic advisor for a university / technical college department. \
Analyze the student's academic record and build the optimal next-term course schedule.

Rules:
- Choose ONLY from "eligible_courses", using their exact codes. Never invent a course.
- Keep total credit hours close to "target_hours" and never above "max_hours" (and at least \
"min_hours" whenever enough eligible hours exist).
- Prioritize:
  1. Bottleneck courses with a high "unlocks_courses" count (check "unlocks_list" to see \
which future courses and graduation/coop requirements they open).
  2. Required courses from earlier levels before higher levels, so the student finishes \
foundational levels cleanly.
  3. Electives ONLY while "elective_hours_remaining" > 0, never exceeding that remaining amount.
- Perform genuine grade & workload analysis:
  - Check the student's grades in "completed_courses", especially direct "prerequisites" of \
each eligible course.
  - Balance "practical"/"mixed" lab-heavy courses with "theoretical" courses so the term \
is achievable.
  - If the student had weak grades (C, D+ or D) in prerequisites or a low GPA, avoid stacking \
too many heavy technical/practical courses at once and add a constructive warning in "warnings".
- For every selected course, write a specific, insightful 1-sentence reason in Modern Standard \
Arabic (reason_ar) and English (reason_en) citing concrete facts from this student's record: \
their exact grade in a prerequisite course, the specific future courses it unlocks, or how it \
balances their term load.
- In Arabic, call a course "مادة" (never "مقرر") and mention course codes accurately.
- summary_ar and summary_en: 2 concise sentences explaining your overall strategy for this \
student (hours chosen, GPA/performance consideration, and progression toward graduation).
- warnings: include actionable academic advice only when warranted (e.g. weak prerequisite \
grade, low GPA cap, or critical bottleneck); otherwise return an empty list.
"""


class _ChoiceOutput(BaseModel):
    code: str
    priority: Priority
    reason_ar: str
    reason_en: str


class _WarningOutput(BaseModel):
    ar: str
    en: str


class _SelectionOutput(BaseModel):
    """Response schema enforced on the model."""

    selected: list[_ChoiceOutput]
    summary_ar: str
    summary_en: str
    warnings: list[_WarningOutput]


def build_payload(context: AdvisorContext) -> dict:
    """Serialise ``context`` into the JSON document sent to the model."""
    plan = context.plan
    return {
        "term": context.term.value,
        "target_hours": context.target_hours,
        "min_hours": context.min_hours,
        "max_hours": context.max_hours,
        "elective_hours_remaining": context.elective_hours_remaining,
        "gpa": context.gpa,
        "completed_courses": [
            {"code": code, "name": plan.by_code[code].name.en, "grade": grade}
            for code, grade in context.grades.items()
        ],
        "eligible_courses": [
            {
                "code": course.code,
                "name": course.name.en,
                "name_ar": course.name.ar,
                "credit_hours": course.credit_hours,
                "level": course.level,
                "type": course.type.value,
                "category": course.category.value,
                "prerequisites": course.prerequisites,
                "corequisites": course.corequisites,
                "unlocks_courses": context.unlock_count(course.code),
                "unlocks_list": plan.unlocks.get(course.code, []),
            }
            for course in context.eligible
        ],
    }


class GeminiAdvisor:
    """Advisor that delegates the choice and the explanations to Gemini."""

    source = RecommendationSource.AI

    def __init__(self, client: JsonModelClient) -> None:
        self._client = client

    async def advise(self, context: AdvisorContext) -> Selection:
        """Ask the model for a schedule.

        Raises:
            AIServiceError: the call failed, timed out, or returned an unusable response.
        """
        output = await self._client.generate(
            system_prompt=SYSTEM_PROMPT,
            contents=json.dumps(build_payload(context), ensure_ascii=False),
            schema=_SelectionOutput,
        )

        return Selection(
            choices=[
                Choice(
                    code=item.code,
                    priority=item.priority,
                    reason=LocalizedText(ar=item.reason_ar, en=item.reason_en),
                )
                for item in output.selected
            ],
            summary=LocalizedText(ar=output.summary_ar, en=output.summary_en),
            warnings=[LocalizedText(ar=item.ar, en=item.en) for item in output.warnings],
        )
