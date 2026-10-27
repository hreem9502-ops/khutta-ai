"""Schemas for the study-plan import used by college staff."""

from enum import StrEnum

from pydantic import BaseModel

from app.models.common import LocalizedText


class PlanIssueCode(StrEnum):
    """Why a plan spreadsheet was rejected. The admin UI translates each code."""

    INVALID_FILE = "invalid_file"
    MISSING_SHEET = "missing_sheet"
    MISSING_COLUMN = "missing_column"
    MISSING_VALUE = "missing_value"
    INVALID_NUMBER = "invalid_number"
    INVALID_CHOICE = "invalid_choice"
    INVALID_DEPARTMENT_CODE = "invalid_department_code"
    DUPLICATE_COURSE = "duplicate_course"
    UNKNOWN_COURSE = "unknown_course"
    SELF_REFERENCE = "self_reference"
    PREREQUISITE_CYCLE = "prerequisite_cycle"
    INVALID_RULES = "invalid_rules"


class PlanIssue(BaseModel):
    """One problem found in an uploaded plan, located as precisely as possible."""

    code: PlanIssueCode
    sheet: str | None = None
    row: int | None = None
    field: str | None = None
    value: str | None = None


class PlanImportSummary(BaseModel):
    code: str
    name: LocalizedText
    total_hours: int
    course_count: int
    level_count: int
    elective_count: int


class PlanImportResult(BaseModel):
    """Outcome of checking (and optionally publishing) a plan spreadsheet."""

    summary: PlanImportSummary | None
    issues: list[PlanIssue]
    published: bool
