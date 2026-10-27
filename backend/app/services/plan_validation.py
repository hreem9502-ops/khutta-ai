"""Structural checks shared by start-up loading and the admin import."""

from collections.abc import Mapping

from app.models.admin import PlanIssue, PlanIssueCode
from app.models.course import StudyPlan

COURSES_SHEET = "courses"


def find_plan_issues(plan: StudyPlan, rows: Mapping[str, int] | None = None) -> list[PlanIssue]:
    """Return every structural problem in ``plan``.

    Checks for duplicate codes, references to unknown courses, courses that require
    themselves, and prerequisite cycles. ``rows`` maps course codes to spreadsheet rows so
    issues can point at the offending line.
    """
    rows = rows or {}
    issues: list[PlanIssue] = []

    def issue(code: PlanIssueCode, course: str, field: str | None = None, value: str | None = None) -> None:
        issues.append(PlanIssue(code=code, sheet=COURSES_SHEET, row=rows.get(course), field=field, value=value))

    seen: set[str] = set()
    for course in plan.courses:
        if course.code in seen:
            issue(PlanIssueCode.DUPLICATE_COURSE, course.code, "code", course.code)
        seen.add(course.code)

    for course in plan.courses:
        for field, references in (("prerequisites", course.prerequisites), ("corequisites", course.corequisites)):
            for reference in references:
                if reference == course.code:
                    issue(PlanIssueCode.SELF_REFERENCE, course.code, field, reference)
                elif reference not in seen:
                    issue(PlanIssueCode.UNKNOWN_COURSE, course.code, field, reference)

    for code in _courses_in_cycles(plan):
        issue(PlanIssueCode.PREREQUISITE_CYCLE, code, "prerequisites")
    return issues


def _courses_in_cycles(plan: StudyPlan) -> list[str]:
    """Codes of courses that are (transitively) their own prerequisite."""
    graph = {course.code: [p for p in course.prerequisites if p != course.code] for course in plan.courses}
    in_cycle: list[str] = []
    for start in graph:
        stack = list(graph.get(start, []))
        visited: set[str] = set()
        while stack:
            current = stack.pop()
            if current == start:
                in_cycle.append(start)
                break
            if current in visited:
                continue
            visited.add(current)
            stack.extend(graph.get(current, []))
    return in_cycle
