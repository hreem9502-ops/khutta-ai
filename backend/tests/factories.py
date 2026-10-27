"""Builders for small synthetic study plans used by unit tests."""

from app.models.course import StudyPlan

DEFAULT_RULES = {
    "gpa_scale": 4.0,
    "min_hours": 12,
    "default_max_hours": 18,
    "high_gpa": {"threshold": 3.5, "max_hours": 21},
    "low_gpa": {"threshold": 2.0, "max_hours": 14},
}


def make_plan(
    courses: list[tuple],
    *,
    elective_hours_required: int = 0,
    rules: dict | None = None,
) -> StudyPlan:
    """Build a plan from ``(code, level, prerequisites, corequisites[, hours[, type]])`` rows."""
    entries = []
    for row in courses:
        code, level, prerequisites, corequisites, *rest = row
        hours = rest[0] if rest else 3
        course_type = rest[1] if len(rest) > 1 else "required"
        entries.append(
            {
                "code": code,
                "name": {"ar": code, "en": code},
                "credit_hours": hours,
                "level": level,
                "type": course_type,
                "category": "mixed",
                "prerequisites": prerequisites,
                "corequisites": corequisites,
                "terms": ["fall", "spring"],
            }
        )
    return StudyPlan.model_validate(
        {
            "code": "test",
            "name": {"ar": "اختبار", "en": "Test"},
            "total_hours": sum(entry["credit_hours"] for entry in entries),
            "elective_hours_required": elective_hours_required,
            "rules": rules or DEFAULT_RULES,
            "courses": entries,
        }
    )
