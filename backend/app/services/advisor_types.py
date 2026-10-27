"""Types shared by the recommendation advisors."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from app.models.common import LocalizedText
from app.models.course import Course, StudyPlan, Term
from app.models.suggestion import Priority, RecommendationSource


@dataclass(frozen=True)
class AdvisorContext:
    """Everything an advisor may base its choice on.

    ``eligible`` has already been filtered by the deterministic rules; an advisor must
    only pick from it.
    """

    plan: StudyPlan
    term: Term
    eligible: list[Course]
    grades: Mapping[str, str | None]
    gpa: float | None
    min_hours: int
    max_hours: int
    target_hours: int
    elective_hours_remaining: int

    def unlock_count(self, code: str) -> int:
        """How many plan courses list ``code`` as a prerequisite."""
        return len(self.plan.unlocks[code])


@dataclass(frozen=True)
class Choice:
    """One course picked by an advisor, with its rationale."""

    code: str
    priority: Priority
    reason: LocalizedText


@dataclass(frozen=True)
class Selection:
    """An advisor's proposed schedule, before validation."""

    choices: list[Choice]
    summary: LocalizedText
    warnings: list[LocalizedText] = field(default_factory=list)


class Advisor(Protocol):
    """Anything that can propose a schedule from the eligible courses."""

    source: RecommendationSource

    async def advise(self, context: AdvisorContext) -> Selection: ...
