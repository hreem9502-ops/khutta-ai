import json

import pytest

from app.errors import AIServiceError
from app.models.student import CourseStatus, TranscriptReader
from app.services.ai_transcript_reader import AITranscriptReader, select_course_lines
from app.services.transcript_service import TranscriptService
from tests.fakes import FakeJsonClient

pytestmark = pytest.mark.anyio

# Grade before credit hours: a layout the rule-based reader deliberately does not trust.
GRADE_FIRST = [
    "Student Name: Sample Student   Student ID: 441000001",
    "CS 101 Introduction to Computing A 3",
    "CS 102 Programming B+ 4",
    "MATH 101 Calculus C 3",
    "ENG 101 English IP 3",
]
STANDARD = [
    "CS 101 Introduction to Computing 3 A",
    "CS 102 Programming 1 4 B+",
    "MATH 101 Calculus 3 C",
]

AI_ANSWER = {
    "courses": [
        {"code": "CS 101", "grade": "A"},
        {"code": "cs102", "grade": "B+"},
        {"code": "MATH 101", "grade": "C"},
        {"code": "ENG 101", "grade": None},
        {"code": "XYZ 999", "grade": "A"},
        {"code": "CS 201", "grade": "excellent-ish"},
    ]
}


def test_personal_lines_are_dropped_and_long_numbers_masked():
    lines = [
        "Student Name: Sample Student",
        "الاسم: طالب تجريبي",
        "Mobile 0551234567",
        "CS 101 Intro 3 A ref 2024001234",
        "Totals 18 hours",
        "Page footer",
    ]

    assert select_course_lines(lines) == ["CS 101 Intro 3 A ref #"]


async def test_reader_keeps_only_plan_courses_with_recognised_grades(cs_plan):
    reader = AITranscriptReader(FakeJsonClient(AI_ANSWER))

    courses = {course.code: course for course in await reader.read(GRADE_FIRST, cs_plan)}

    assert set(courses) == {"CS 101", "CS 102", "MATH 101", "ENG 101", "CS 201"}
    assert courses["CS 102"].status is CourseStatus.PASSED
    assert courses["ENG 101"].status is CourseStatus.IN_PROGRESS
    assert courses["CS 201"].grade is None  # unknown grade words are not trusted


async def test_reader_never_sends_personal_lines(cs_plan):
    client = FakeJsonClient(AI_ANSWER)

    await AITranscriptReader(client).read(GRADE_FIRST, cs_plan)

    sent = json.loads(client.calls[0]["contents"])
    assert all("Student" not in line and "441000001" not in line for line in sent["lines"])
    assert "CS 101" in sent["known_codes"]


async def test_service_uses_ai_when_rules_find_no_grades(cs_plan, make_pdf):
    service = TranscriptService(AITranscriptReader(FakeJsonClient(AI_ANSWER)))

    result = await service.parse(make_pdf(GRADE_FIRST), cs_plan)

    assert result.reader is TranscriptReader.AI
    assert {c.code for c in result.courses if c.status is CourseStatus.PASSED} == {"CS 101", "CS 102", "MATH 101"}


async def test_service_skips_ai_when_rules_read_the_layout(cs_plan, make_pdf):
    client = FakeJsonClient(AI_ANSWER)

    result = await TranscriptService(AITranscriptReader(client)).parse(make_pdf(STANDARD), cs_plan)

    assert result.reader is TranscriptReader.RULES
    assert client.calls == []


async def test_service_keeps_rule_result_when_ai_fails(cs_plan, make_pdf):
    service = TranscriptService(AITranscriptReader(FakeJsonClient(error=AIServiceError("down"))))

    result = await service.parse(make_pdf(GRADE_FIRST), cs_plan)

    assert result.reader is TranscriptReader.RULES
    assert result.courses  # codes were still found, just without grades


async def test_service_without_ai_returns_rule_result(cs_plan, make_pdf):
    result = await TranscriptService(None).parse(make_pdf(GRADE_FIRST), cs_plan)

    assert result.reader is TranscriptReader.RULES
