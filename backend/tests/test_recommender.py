import pytest

from app.errors import AIServiceError, UnknownCourseError
from app.models.common import LocalizedText
from app.models.suggestion import (
    CompletedCourse,
    Priority,
    RecommendationRequest,
    RecommendationSource,
)
from app.services.advisor_types import AdvisorContext, Choice, Selection
from app.services.plan_repository import PlanRepository
from app.services.recommender import RecommendationService
from app.services.rule_advisor import RuleBasedAdvisor
from tests.factories import make_plan

pytestmark = pytest.mark.anyio

TEXT = LocalizedText(ar="سبب", en="reason")
FIRST_SEMESTER = ["CS 101", "CS 102", "MATH 101", "ENG 101", "ISL 101"]


class ScriptedAdvisor:
    """Advisor that returns a fixed list of codes, standing in for the AI model."""

    source = RecommendationSource.AI

    def __init__(self, codes: list[str] | None = None, error: Exception | None = None) -> None:
        self.codes = codes or []
        self.error = error

    async def advise(self, context: AdvisorContext) -> Selection:
        if self.error:
            raise self.error
        return Selection(
            choices=[Choice(code, Priority.HIGH, TEXT) for code in self.codes],
            summary=LocalizedText(ar="ملخص", en="summary"),
        )


def request(completed: list[str], *, gpa: float | None = None, department: str = "cs", **extra):
    return RecommendationRequest(
        department=department,
        term="fall",
        completed=[CompletedCourse(code=code, grade="B") for code in completed],
        gpa=gpa,
        **extra,
    )


def service(plans: PlanRepository, advisor) -> RecommendationService:
    return RecommendationService(plans, primary=advisor, fallback=RuleBasedAdvisor())


async def test_ai_picks_that_are_valid_are_kept_with_their_reasons(repository):
    advisor = ScriptedAdvisor(["CS 201", "CS 202", "MATH 201", "ENG 102"])

    result = await service(repository, advisor).recommend(request(FIRST_SEMESTER))

    assert result.source is RecommendationSource.AI
    assert [course.code for course in result.courses][:4] == ["CS 201", "CS 202", "MATH 201", "ENG 102"]
    assert result.courses[0].reason == TEXT


async def test_ineligible_unknown_and_duplicate_picks_are_dropped(repository):
    advisor = ScriptedAdvisor(["CS 201", "CS 201", "CS 301", "NOPE 999", "CS 202", "MATH 201", "ENG 102"])

    result = await service(repository, advisor).recommend(request(FIRST_SEMESTER))

    codes = [course.code for course in result.courses]
    assert codes.count("CS 201") == 1
    assert "CS 301" not in codes  # prerequisites CS 201 / CS 202 are not passed
    assert "NOPE 999" not in codes


async def test_total_hours_never_exceed_the_gpa_limit(repository):
    everything_eligible = [
        "CS 201", "CS 202", "MATH 201", "ENG 102", "ARB 101", "NET 201", "ISL 201", "CS 301",
    ]
    advisor = ScriptedAdvisor(everything_eligible)

    result = await service(repository, advisor).recommend(request(FIRST_SEMESTER, gpa=1.8))

    assert result.max_hours == 14
    assert result.total_hours <= 14


async def test_load_below_minimum_is_topped_up_from_the_rule_ranking(repository):
    advisor = ScriptedAdvisor(["CS 201"])  # only 4 hours

    result = await service(repository, advisor).recommend(request(FIRST_SEMESTER))

    assert result.total_hours >= result.min_hours
    assert result.courses[0].code == "CS 201"
    assert any("minimum" in warning.en for warning in result.warnings)


async def test_failing_advisor_falls_back_to_rules(repository):
    advisor = ScriptedAdvisor(error=AIServiceError("timeout"))

    result = await service(repository, advisor).recommend(request(FIRST_SEMESTER))

    assert result.source is RecommendationSource.RULES
    assert result.courses
    assert result.min_hours <= result.total_hours <= result.max_hours


async def test_advisor_answer_with_no_usable_course_falls_back_to_rules(repository):
    advisor = ScriptedAdvisor(["CS 801", "NOPE 1"])

    result = await service(repository, advisor).recommend(request(FIRST_SEMESTER))

    assert result.source is RecommendationSource.RULES


async def test_every_recommended_course_has_its_prerequisites_passed(repository):
    result = await service(repository, RuleBasedAdvisor()).recommend(request(FIRST_SEMESTER))

    plan = repository.get("cs")
    for course in result.courses:
        assert set(plan.by_code[course.code].prerequisites) <= set(FIRST_SEMESTER)


async def test_elective_hours_are_capped_at_the_remaining_requirement(repository):
    plan = repository.get("cs")
    all_required_before_6 = [
        course.code for course in plan.courses if course.type == "required" and course.level < 6
    ]
    advisor = ScriptedAdvisor(["CS 510", "CS 520", "CS 530", "CS 601"])
    done = [*all_required_before_6, "CS 540", "CS 550", "CS 560"]  # 9 of 12 elective hours

    result = await service(repository, advisor).recommend(request(done))

    elective_hours = sum(course.credit_hours for course in result.courses if course.type == "elective")
    assert elective_hours <= 3


async def test_no_eligible_courses_returns_an_empty_schedule_with_a_warning(repository):
    plan = repository.get("cs")
    everything = [course.code for course in plan.courses]

    result = await service(repository, RuleBasedAdvisor()).recommend(request(everything))

    assert result.courses == []
    assert result.progress.remaining_required_courses == 0
    assert result.warnings


async def test_progress_reports_hours_and_remaining_required_courses(repository):
    plan = repository.get("cs")
    required = [course for course in plan.courses if course.type == "required"]

    result = await service(repository, RuleBasedAdvisor()).recommend(request(["CS 101", "CS 102"]))

    assert result.progress.completed_hours == 7
    assert result.progress.total_hours == plan.total_hours
    assert result.progress.remaining_required_courses == len(required) - 2


async def test_blocked_courses_name_their_missing_prerequisites(repository):
    result = await service(repository, RuleBasedAdvisor()).recommend(request(["CS 101", "CS 102"]))

    blocked = {course.code: course for course in result.blocked}
    assert blocked["CS 301"].missing_prerequisites == ["CS 201", "CS 202"]


async def test_unknown_completed_course_is_rejected(repository):
    with pytest.raises(UnknownCourseError):
        await service(repository, RuleBasedAdvisor()).recommend(request(["CS 101", "XX 999"]))


async def test_corequisite_pairs_are_scheduled_together_or_not_at_all():
    plan = make_plan(
        [
            ("A 101", 1, [], [], 4),
            ("LAB 101", 1, [], ["A 101"], 3),
            ("B 101", 1, [], [], 4),
            ("C 101", 1, [], [], 4),
            ("D 101", 1, [], [], 4),
        ]
    )
    plans = PlanRepository([plan])
    advisor = ScriptedAdvisor(["LAB 101", "B 101", "C 101", "D 101"])  # lab picked without its lecture

    result = await service(plans, advisor).recommend(request([], department="test"))

    codes = [course.code for course in result.courses]
    assert "LAB 101" not in codes or "A 101" in codes
