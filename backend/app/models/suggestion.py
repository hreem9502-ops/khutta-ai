"""Request and response schemas for course recommendations."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.models.common import LocalizedText, normalize_course_code
from app.models.course import CourseCategory, CourseType, Term


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationSource(StrEnum):
    """Who ranked and explained the selection."""

    AI = "ai"
    RULES = "rules"


class CompletedCourse(BaseModel):
    """A course the student has passed."""

    code: str
    grade: str | None = None

    _normalize_code = field_validator("code")(normalize_course_code)


class RecommendationRequest(BaseModel):
    """Everything the recommender needs; no personal identifiers are accepted."""

    department: str
    term: Term
    completed: list[CompletedCourse]
    in_progress: list[str] = []
    gpa: float | None = Field(default=None, ge=0, le=5)

    @field_validator("in_progress")
    @classmethod
    def _normalize_in_progress(cls, codes: list[str]) -> list[str]:
        return [normalize_course_code(code) for code in codes]


class RecommendedCourse(BaseModel):
    code: str
    name: LocalizedText
    credit_hours: int
    level: int
    type: CourseType
    category: CourseCategory
    priority: Priority
    reason: LocalizedText


class BlockedCourse(BaseModel):
    """A course the student cannot take yet because prerequisites are missing."""

    code: str
    name: LocalizedText
    level: int
    missing_prerequisites: list[str]


class Progress(BaseModel):
    completed_hours: int
    total_hours: int
    remaining_required_courses: int


class Recommendation(BaseModel):
    courses: list[RecommendedCourse]
    total_hours: int
    min_hours: int
    max_hours: int
    summary: LocalizedText
    warnings: list[LocalizedText]
    blocked: list[BlockedCourse]
    progress: Progress
    source: RecommendationSource
