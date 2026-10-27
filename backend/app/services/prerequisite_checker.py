"""Deterministic eligibility rules.

Everything the student is told they *may* register for is decided here, never by the
language model. The advisor only chooses among the courses this module approves.
"""

from collections.abc import Collection, Iterable
from dataclasses import dataclass

from app.models.course import Course, CourseType, StudyPlan, Term


@dataclass(frozen=True)
class BlockedEntry:
    """A course offered this term whose prerequisites are not all passed yet."""

    course: Course
    missing_prerequisites: list[str]


@dataclass(frozen=True)
class EligibilityReport:
    eligible: list[Course]
    blocked: list[BlockedEntry]


def check_eligibility(
    plan: StudyPlan,
    completed: Collection[str],
    in_progress: Collection[str],
    term: Term,
) -> EligibilityReport:
    """Split the not-yet-taken courses offered in ``term`` into eligible and blocked.

    A course is eligible when every prerequisite is in ``completed``. Courses already
    passed or currently in progress are never offered again.
    """
    taken = set(completed) | set(in_progress)
    eligible: list[Course] = []
    blocked: list[BlockedEntry] = []

    for course in plan.courses:
        if course.code in taken or term not in course.terms:
            continue
        missing = [code for code in course.prerequisites if code not in completed]
        if missing:
            blocked.append(BlockedEntry(course, missing))
        else:
            eligible.append(course)

    return EligibilityReport(eligible, blocked)


def remaining_elective_hours(plan: StudyPlan, taken: Iterable[str]) -> int:
    """Elective hours the student still needs, counting passed and in-progress electives."""
    done = sum(
        plan.by_code[code].credit_hours
        for code in taken
        if code in plan.by_code and plan.by_code[code].type is CourseType.ELECTIVE
    )
    return max(plan.elective_hours_required - done, 0)


def enforce_corequisites(
    plan: StudyPlan,
    selected: list[str],
    completed: Collection[str],
) -> list[str]:
    """Drop selected courses whose corequisites are neither passed nor also selected.

    Removal can orphan another course's corequisite, so this repeats until stable.
    Order of ``selected`` is preserved.
    """
    remaining = list(selected)
    changed = True
    while changed:
        changed = False
        available = set(completed) | set(remaining)
        for code in list(remaining):
            if any(co not in available for co in plan.by_code[code].corequisites):
                remaining.remove(code)
                changed = True
                break
    return remaining
