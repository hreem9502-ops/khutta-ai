"""Serves the department study plans and keeps them in sync with their store."""

import time
from collections.abc import Callable

from app.errors import DepartmentNotFoundError
from app.models.course import DepartmentSummary, StudyPlan
from app.services.plan_store import PlanStore
from app.services.plan_validation import find_plan_issues


class PlanRepository:
    """In-memory view of the study plans, validated on load and on save.

    With ``refresh_seconds`` set, the view is re-read from the store once it is older than
    that, so a plan published on one server instance reaches the others.
    """

    def __init__(
        self,
        plans: list[StudyPlan],
        store: PlanStore | None = None,
        refresh_seconds: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._store = store
        self._refresh_seconds = refresh_seconds
        self._clock = clock
        self._replace(plans)

    @classmethod
    def from_store(cls, store: PlanStore, refresh_seconds: float | None = None) -> "PlanRepository":
        """Load every plan from ``store``; :meth:`save` writes back to it."""
        return cls(store.load_all(), store, refresh_seconds)

    def list_departments(self) -> list[DepartmentSummary]:
        self._refresh_if_stale()
        return [
            DepartmentSummary(code=plan.code, name=plan.name, total_hours=plan.total_hours)
            for plan in self._plans.values()
        ]

    def get(self, code: str) -> StudyPlan:
        """Return the plan for ``code`` or raise :class:`DepartmentNotFoundError`."""
        self._refresh_if_stale()
        try:
            return self._plans[code]
        except KeyError:
            raise DepartmentNotFoundError(f"No study plan for department '{code}'") from None

    def save(self, plan: StudyPlan) -> None:
        """Validate ``plan``, persist it, and make it live immediately."""
        if self._store is None:
            raise RuntimeError("This repository has no store to save to")
        self._validate(plan)
        self._store.save(plan)
        self._plans[plan.code] = plan

    def _refresh_if_stale(self) -> None:
        if self._store is None or self._refresh_seconds is None:
            return
        if self._clock() - self._loaded_at >= self._refresh_seconds:
            self._replace(self._store.load_all())

    def _replace(self, plans: list[StudyPlan]) -> None:
        for plan in plans:
            self._validate(plan)
        self._plans = {plan.code: plan for plan in plans}
        self._loaded_at = self._clock()

    @staticmethod
    def _validate(plan: StudyPlan) -> None:
        issues = find_plan_issues(plan)
        if issues:
            details = ", ".join(f"{issue.code}({issue.value or issue.field})" for issue in issues)
            raise ValueError(f"Plan '{plan.code}' is invalid: {details}")
