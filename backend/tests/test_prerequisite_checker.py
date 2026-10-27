from app.models.course import Term
from app.services.prerequisite_checker import (
    check_eligibility,
    enforce_corequisites,
    remaining_elective_hours,
)
from tests.factories import make_plan


def codes(courses) -> set[str]:
    return {course.code for course in courses}


def test_first_semester_student_sees_only_courses_without_prerequisites(cs_plan):
    report = check_eligibility(cs_plan, completed=[], in_progress=[], term=Term.FALL)

    assert codes(report.eligible) == {
        "CS 101", "CS 102", "MATH 101", "ENG 101", "ISL 101", "ARB 101",
    }


def test_course_unlocks_once_every_prerequisite_is_passed(cs_plan):
    only_one = check_eligibility(cs_plan, ["CS 201"], [], Term.FALL)
    both = check_eligibility(cs_plan, ["CS 201", "CS 202"], [], Term.FALL)

    assert "CS 301" not in codes(only_one.eligible)
    assert "CS 301" in codes(both.eligible)


def test_blocked_entry_lists_only_the_missing_prerequisites(cs_plan):
    report = check_eligibility(cs_plan, ["CS 201"], [], Term.FALL)

    entry = next(entry for entry in report.blocked if entry.course.code == "CS 301")
    assert entry.missing_prerequisites == ["CS 202"]


def test_passed_and_in_progress_courses_are_never_offered_again(cs_plan):
    report = check_eligibility(cs_plan, ["CS 101"], ["CS 102"], Term.FALL)

    offered = codes(report.eligible) | codes(entry.course for entry in report.blocked)
    assert "CS 101" not in offered
    assert "CS 102" not in offered


def test_in_progress_prerequisite_does_not_unlock_dependents(cs_plan):
    report = check_eligibility(cs_plan, [], ["CS 102"], Term.FALL)

    assert "CS 201" not in codes(report.eligible)


def test_courses_outside_the_term_are_excluded(cs_plan):
    fall = check_eligibility(cs_plan, _everything_before(cs_plan, 5), [], Term.FALL)
    spring = check_eligibility(cs_plan, _everything_before(cs_plan, 5), [], Term.SPRING)

    assert "CS 501" in codes(fall.eligible)  # level 5 runs in fall
    assert "CS 501" not in codes(spring.eligible)
    assert "CS 602" in codes(spring.eligible)  # level 6 runs in spring


def test_remaining_elective_hours_counts_passed_and_in_progress_electives(cs_plan):
    assert remaining_elective_hours(cs_plan, []) == 12
    assert remaining_elective_hours(cs_plan, ["CS 510", "CS 520"]) == 6
    assert remaining_elective_hours(cs_plan, ["CS 510", "CS 520", "CS 530", "CS 540", "CS 550"]) == 0


def test_corequisite_must_be_selected_together_or_already_passed():
    plan = make_plan(
        [
            ("A 101", 1, [], []),
            ("B 101", 1, [], []),
            ("A 102", 2, [], ["B 101"]),
        ]
    )

    assert enforce_corequisites(plan, ["A 102"], completed=[]) == []
    assert enforce_corequisites(plan, ["A 102", "B 101"], completed=[]) == ["A 102", "B 101"]
    assert enforce_corequisites(plan, ["A 102"], completed=["B 101"]) == ["A 102"]


def test_dropping_a_course_cascades_to_courses_that_needed_it_as_corequisite():
    plan = make_plan(
        [
            ("A 101", 1, [], ["B 101"]),  # needs B 101, which itself needs C 101
            ("B 101", 1, [], ["C 101"]),
            ("C 101", 1, [], []),
        ]
    )

    assert enforce_corequisites(plan, ["A 101", "B 101"], completed=[]) == []


def _everything_before(plan, level: int) -> list[str]:
    return [course.code for course in plan.courses if course.level < level and course.type == "required"]
