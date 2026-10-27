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
You are an academic advisor for a university department. Decide which courses a student \
should register for next term.

Rules:
- Choose ONLY from "eligible_courses", using their exact codes. Never invent a course.
- The total credit hours should be close to "target_hours" and must never exceed "max_hours".
- Prefer required courses over electives and lower levels over higher levels. Give extra \
weight to courses with a high "unlocks_courses" count, because they open later courses.
- Select electives only while "elective_hours_remaining" is above zero, and never more \
elective hours than that.
- Use the student's grades to balance the workload. If grades in related earlier courses \
are weak (C or below) or the GPA is low, avoid stacking several demanding courses of the \
same category together.
- For every selected course write one short sentence of reasoning in Modern Standard \
Arabic (reason_ar) and in English (reason_en) that cites a concrete fact: a prior grade, \
a course it unlocks, or its level.
- In Arabic, call a course "مادة" (never "مقرر") and refer to courses by their code.
- summary_ar and summary_en: at most two sentences describing the logic of the schedule.
- warnings: genuine concerns only. Return an empty list when there are none.
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
                "credit_hours": course.credit_hours,
                "level": course.level,
                "type": course.type.value,
                "category": course.category.value,
                "unlocks_courses": context.unlock_count(course.code),
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
