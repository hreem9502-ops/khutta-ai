"""Schemas for transcript parsing."""

from enum import StrEnum

from pydantic import BaseModel, Field


class CourseStatus(StrEnum):
    """What a transcript line says about a course."""

    PASSED = "passed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class TranscriptCourse(BaseModel):
    """A plan course found in an uploaded transcript."""

    code: str
    grade: str | None = None
    status: CourseStatus


class TranscriptReader(StrEnum):
    """Which reader produced the course list."""

    RULES = "rules"
    AI = "ai"


class ParsedTranscript(BaseModel):
    """Result of reading a transcript PDF against a study plan."""

    department: str
    courses: list[TranscriptCourse]
    gpa: float | None = Field(default=None, description="Cumulative GPA if the PDF states one.")
    reader: TranscriptReader = TranscriptReader.RULES
