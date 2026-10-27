import json

import pytest

from app.errors import AIServiceError
from app.models.course import Term
from app.models.suggestion import Priority
from app.services.advisor_types import AdvisorContext
from app.services.ai_advisor import GeminiAdvisor, build_payload
from app.services.prerequisite_checker import check_eligibility
from tests.fakes import FakeJsonClient

pytestmark = pytest.mark.anyio

GRADES = {"CS 101": "A", "CS 102": "C+", "MATH 101": "B"}

MODEL_ANSWER = {
    "selected": [
        {"code": "CS 201", "priority": "high", "reason_ar": "تكملة برمجة 1", "reason_en": "Follows Programming 1."},
    ],
    "summary_ar": "ملخص",
    "summary_en": "Summary",
    "warnings": [{"ar": "تنبيه", "en": "Heads up"}],
}


@pytest.fixture
def context(cs_plan) -> AdvisorContext:
    eligible = check_eligibility(cs_plan, GRADES, [], Term.FALL).eligible
    return AdvisorContext(
        plan=cs_plan,
        term=Term.FALL,
        eligible=eligible,
        grades=GRADES,
        gpa=3.1,
        min_hours=12,
        max_hours=18,
        target_hours=15,
        elective_hours_remaining=12,
    )


def test_payload_contains_only_codes_names_and_grades(context):
    payload = build_payload(context)

    assert payload["completed_courses"][1] == {"code": "CS 102", "name": "Programming 1", "grade": "C+"}
    assert {course["code"] for course in payload["eligible_courses"]} == {course.code for course in context.eligible}
    assert set(payload) == {
        "term", "target_hours", "min_hours", "max_hours",
        "elective_hours_remaining", "gpa", "completed_courses", "eligible_courses",
    }


async def test_converts_the_model_answer_into_a_selection(context):
    client = FakeJsonClient(MODEL_ANSWER)

    selection = await GeminiAdvisor(client).advise(context)

    assert selection.choices[0].code == "CS 201"
    assert selection.choices[0].priority is Priority.HIGH
    assert selection.choices[0].reason.ar == "تكملة برمجة 1"
    assert selection.warnings[0].en == "Heads up"
    assert json.loads(client.calls[0]["contents"])["term"] == "fall"


async def test_client_failures_propagate_as_ai_service_errors(context):
    with pytest.raises(AIServiceError):
        await GeminiAdvisor(FakeJsonClient(error=AIServiceError("down"))).advise(context)
