"""Independent re-check of a recommendation against the study plan.

This deliberately does not reuse the recommender's own validation: it re-derives every
hard rule from the plan data, so a bug in the production checks shows up here as a
violation instead of being repeated.
"""

from app.models.course import StudyPlan, Term
from app.models.suggestion import Recommendation


def max_hours_allowed(plan: StudyPlan, gpa: float | None) -> int:
    rules = plan.rules
    if gpa is None:
        return rules.default_max_hours
    if gpa >= rules.high_gpa.threshold:
        return rules.high_gpa.max_hours
    if gpa < rules.low_gpa.threshold:
        return rules.low_gpa.max_hours
    return rules.default_max_hours


def audit_recommendation(
    plan: StudyPlan,
    recommendation: Recommendation,
    *,
    passed: set[str],
    in_progress: set[str],
    term: Term,
    gpa: float | None,
) -> list[str]:
    """Return a human-readable line for every hard rule the recommendation breaks."""
    violations: list[str] = []
    codes = [course.code for course in recommendation.courses]
    selected = set(codes)

    if len(codes) != len(selected):
        violations.append("duplicate course in schedule")

    for code in codes:
        course = plan.by_code.get(code)
        if course is None:
            violations.append(f"{code}: not in the study plan")
            continue
        if code in passed:
            violations.append(f"{code}: already passed")
        if code in in_progress:
            violations.append(f"{code}: currently in progress")
        if term not in course.terms:
            violations.append(f"{code}: not offered in {term.value}")
        missing = [p for p in course.prerequisites if p not in passed]
        if missing:
            violations.append(f"{code}: missing prerequisites {', '.join(missing)}")
        unmet = [c for c in course.corequisites if c not in passed and c not in selected]
        if unmet:
            violations.append(f"{code}: corequisites neither passed nor scheduled: {', '.join(unmet)}")

    hours = sum(plan.by_code[code].credit_hours for code in selected if code in plan.by_code)
    if hours != recommendation.total_hours:
        violations.append(f"reported total {recommendation.total_hours} h but courses add up to {hours} h")
    allowed = max_hours_allowed(plan, gpa)
    if hours > allowed:
        violations.append(f"load {hours} h exceeds the {allowed} h maximum")

    elective_done = sum(
        plan.by_code[code].credit_hours
        for code in passed | in_progress
        if code in plan.by_code and plan.by_code[code].type == "elective"
    )
    elective_selected = sum(
        plan.by_code[code].credit_hours
        for code in selected
        if code in plan.by_code and plan.by_code[code].type == "elective"
    )
    elective_remaining = max(plan.elective_hours_required - elective_done, 0)
    if elective_selected > elective_remaining:
        violations.append(f"{elective_selected} elective hours scheduled but only {elective_remaining} remain")

    return violations
