"""Study plan and course definitions loaded from ``app/data/plans``."""

from enum import StrEnum
from functools import cached_property

from pydantic import BaseModel, Field

from app.models.common import LocalizedText


class Term(StrEnum):
    """Academic terms in which a course may be offered."""

    FALL = "fall"
    SPRING = "spring"


class CourseType(StrEnum):
    REQUIRED = "required"
    ELECTIVE = "elective"


class CourseCategory(StrEnum):
    THEORETICAL = "theoretical"
    PRACTICAL = "practical"
    MIXED = "mixed"


class Course(BaseModel):
    """One course in a department's study plan."""

    code: str
    name: LocalizedText
    credit_hours: int = Field(gt=0)
    level: int = Field(ge=1)
    type: CourseType
    category: CourseCategory
    prerequisites: list[str] = []
    corequisites: list[str] = []
    terms: list[Term]


class GpaTier(BaseModel):
    """A credit-hour ceiling that applies once the GPA crosses ``threshold``."""

    threshold: float
    max_hours: int


class CreditRules(BaseModel):
    """Registration load rules for a department."""

    gpa_scale: float
    min_hours: int
    default_max_hours: int
    high_gpa: GpaTier
    low_gpa: GpaTier

    def max_hours_for(self, gpa: float | None) -> int:
        """Return the maximum registrable hours for a student with the given GPA."""
        if gpa is None:
            return self.default_max_hours
        if gpa >= self.high_gpa.threshold:
            return self.high_gpa.max_hours
        if gpa < self.low_gpa.threshold:
            return self.low_gpa.max_hours
        return self.default_max_hours


class StudyPlan(BaseModel):
    """A department's full study plan."""

    code: str
    name: LocalizedText
    total_hours: int
    elective_hours_required: int
    rules: CreditRules
    courses: list[Course]

    @cached_property
    def by_code(self) -> dict[str, Course]:
        """Courses indexed by canonical code."""
        return {course.code: course for course in self.courses}

    @cached_property
    def unlocks(self) -> dict[str, list[str]]:
        """For each course, the codes of courses that list it as a prerequisite."""
        result: dict[str, list[str]] = {course.code: [] for course in self.courses}
        for course in self.courses:
            for prerequisite in course.prerequisites:
                result[prerequisite].append(course.code)
        return result


class DepartmentSummary(BaseModel):
    """Lightweight department listing for selection menus."""

    code: str
    name: LocalizedText
    total_hours: int
