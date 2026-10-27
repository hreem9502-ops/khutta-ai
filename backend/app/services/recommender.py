"""Orchestrates a recommendation: deterministic eligibility, advisor, then validation.

The advisor (AI or rule-based) proposes a schedule, but nothing it returns reaches the
student until :meth:`RecommendationService._validate` has re-checked it against the
eligibility rules and the credit-hour limits.
"""

import logging

from app.constants import MAX_BLOCKED_COURSES
from app.errors import AIServiceError, UnknownCourseError
from app.models.common import LocalizedText
from app.models.course import Course, CourseType, StudyPlan
from app.models.suggestion import (
    BlockedCourse,
    Progress,
    Recommendation,
    RecommendationRequest,
    RecommendationSource,
    RecommendedCourse,
)
from app.services.advisor_types import Advisor, AdvisorContext, Choice, Selection
from app.services.plan_repository import PlanRepository
from app.services.prerequisite_checker import (
    EligibilityReport,
    check_eligibility,
    enforce_corequisites,
    remaining_elective_hours,
)
from app.services.rule_advisor import describe_course, rank_courses

logger = logging.getLogger(__name__)


class RecommendationService:
    """Builds validated recommendations for a student."""

    def __init__(self, plans: PlanRepository, primary: Advisor, fallback: Advisor) -> None:
        self._plans = plans
        self._primary = primary
        self._fallback = fallback

    async def recommend(self, request: RecommendationRequest) -> Recommendation:
        """Return a schedule for ``request`` that always satisfies the plan's rules."""
        plan = self._plans.get(request.department)
        grades = {item.code: item.grade for item in request.completed}
        self._require_known_courses(plan, [*grades, *request.in_progress])

        eligibility = check_eligibility(plan, grades, request.in_progress, request.term)
        context = self._build_context(plan, request, eligibility, grades)

        selection, source = await self._advise(context)
        courses, warnings = self._validate(context, selection)

        total_hours = sum(course.credit_hours for course in courses)
        warnings = [*warnings, *self._load_warnings(context, request, total_hours, bool(eligibility.eligible))]

        return Recommendation(
            courses=courses,
            total_hours=total_hours,
            min_hours=context.min_hours,
            max_hours=context.max_hours,
            summary=selection.summary,
            warnings=warnings,
            blocked=self._blocked_courses(eligibility),
            progress=self._progress(plan, grades),
            source=source,
        )

    @staticmethod
    def _require_known_courses(plan: StudyPlan, codes: list[str]) -> None:
        unknown = sorted({code for code in codes if code not in plan.by_code})
        if unknown:
            raise UnknownCourseError(f"Not in the {plan.code} plan: {', '.join(unknown)}")

    @staticmethod
    def _build_context(
        plan: StudyPlan,
        request: RecommendationRequest,
        eligibility: EligibilityReport,
        grades: dict[str, str | None],
    ) -> AdvisorContext:
        min_hours = plan.rules.min_hours
        max_hours = plan.rules.max_hours_for(request.gpa)
        elective_remaining = remaining_elective_hours(plan, [*grades, *request.in_progress])

        eligible = [
            course
            for course in eligibility.eligible
            if course.type is CourseType.REQUIRED or elective_remaining > 0
        ]
        return AdvisorContext(
            plan=plan,
            term=request.term,
            eligible=eligible,
            grades=grades,
            gpa=request.gpa,
            min_hours=min_hours,
            max_hours=max_hours,
            target_hours=round((min_hours + max_hours) / 2),
            elective_hours_remaining=elective_remaining,
        )

    async def _advise(self, context: AdvisorContext) -> tuple[Selection, RecommendationSource]:
        """Use the primary advisor, falling back to rules if it fails or returns nothing."""
        if context.eligible:
            try:
                selection = await self._primary.advise(context)
                if self._usable_choices(context, selection):
                    return selection, self._primary.source
                logger.warning("Primary advisor returned no eligible courses; using rules")
            except AIServiceError as error:
                logger.warning("Primary advisor failed (%s); using rules", error)
        return await self._fallback.advise(context), self._fallback.source

    @staticmethod
    def _usable_choices(context: AdvisorContext, selection: Selection) -> bool:
        eligible_codes = {course.code for course in context.eligible}
        return any(choice.code in eligible_codes for choice in selection.choices)

    def _validate(
        self,
        context: AdvisorContext,
        selection: Selection,
    ) -> tuple[list[RecommendedCourse], list[LocalizedText]]:
        """Reduce ``selection`` to a schedule that satisfies every hard rule.

        Steps, in order: drop unknown, ineligible and duplicate picks; drop electives beyond
        the remaining elective hours; drop picks with unmet corequisites; trim from the end
        until the load fits ``max_hours``; top up from the rule ranking if below ``min_hours``.
        """
        eligible = {course.code: course for course in context.eligible}
        chosen: dict[str, Choice] = {}
        for choice in selection.choices:
            if choice.code in eligible and choice.code not in chosen:
                chosen[choice.code] = choice

        codes = self._limit_electives(context, list(chosen))
        codes = enforce_corequisites(context.plan, codes, context.grades)
        codes = self._trim_to_max(context, codes)
        additions = self._top_up(context, codes)
        codes += [choice.code for choice in additions]
        chosen.update({choice.code: choice for choice in additions})

        courses = [self._to_recommended(eligible[code], chosen[code]) for code in codes]
        warnings = list(selection.warnings)
        if additions:
            warnings.append(
                LocalizedText(
                    ar="أُضيفت مواد إضافية لبلوغ الحد الأدنى للساعات المسموح بتسجيلها.",
                    en="Extra courses were added to reach the minimum registration load.",
                )
            )
        return courses, warnings

    @staticmethod
    def _limit_electives(context: AdvisorContext, codes: list[str]) -> list[str]:
        budget = context.elective_hours_remaining
        kept: list[str] = []
        for code in codes:
            course = context.plan.by_code[code]
            if course.type is CourseType.ELECTIVE:
                if course.credit_hours > budget:
                    continue
                budget -= course.credit_hours
            kept.append(code)
        return kept

    @staticmethod
    def _trim_to_max(context: AdvisorContext, codes: list[str]) -> list[str]:
        """Remove the least important picks (electives first, then highest level) until it fits."""
        remaining = list(codes)

        def hours() -> int:
            return sum(context.plan.by_code[code].credit_hours for code in remaining)

        while remaining and hours() > context.max_hours:
            victim = max(
                remaining,
                key=lambda code: (
                    context.plan.by_code[code].type is CourseType.ELECTIVE,
                    context.plan.by_code[code].level,
                ),
            )
            remaining.remove(victim)
        return remaining

    @staticmethod
    def _top_up(context: AdvisorContext, codes: list[str]) -> list[Choice]:
        """Pick extra ranked courses while the load is below the minimum and still fits."""
        by_code = context.plan.by_code
        selected = set(codes)
        total = sum(by_code[code].credit_hours for code in codes)
        elective_budget = context.elective_hours_remaining - sum(
            by_code[code].credit_hours for code in codes if by_code[code].type is CourseType.ELECTIVE
        )
        additions: list[Choice] = []

        for course in rank_courses(context):
            if total >= context.min_hours:
                break
            if course.code in selected or total + course.credit_hours > context.max_hours:
                continue
            if not set(course.corequisites) <= selected | set(context.grades):
                continue
            if course.type is CourseType.ELECTIVE:
                if course.credit_hours > elective_budget:
                    continue
                elective_budget -= course.credit_hours
            additions.append(describe_course(context, course))
            selected.add(course.code)
            total += course.credit_hours

        return additions

    @staticmethod
    def _to_recommended(course: Course, choice: Choice) -> RecommendedCourse:
        return RecommendedCourse(
            code=course.code,
            name=course.name,
            credit_hours=course.credit_hours,
            level=course.level,
            type=course.type,
            category=course.category,
            priority=choice.priority,
            reason=choice.reason,
        )

    @staticmethod
    def _load_warnings(
        context: AdvisorContext,
        request: RecommendationRequest,
        total_hours: int,
        has_eligible: bool,
    ) -> list[LocalizedText]:
        warnings: list[LocalizedText] = []
        if not has_eligible:
            warnings.append(
                LocalizedText(
                    ar="لا توجد مواد متاحة لك في هذا الفصل. راجع المرشد الأكاديمي.",
                    en="No courses are available to you this term. Please see your academic advisor.",
                )
            )
        elif total_hours < context.min_hours:
            warnings.append(
                LocalizedText(
                    ar=f"مجموع الساعات ({total_hours}) أقل من الحد الأدنى ({context.min_hours}) لأن المواد المتاحة لك محدودة.",
                    en=f"The load ({total_hours} hours) is below the {context.min_hours}-hour minimum because few courses are open to you.",
                )
            )
        if request.gpa is not None and context.max_hours != context.plan.rules.default_max_hours:
            warnings.append(
                LocalizedText(
                    ar=f"الحد الأقصى للساعات {context.max_hours} بحسب معدلك التراكمي.",
                    en=f"Your maximum load is {context.max_hours} hours based on your GPA.",
                )
            )
        return warnings

    @staticmethod
    def _blocked_courses(eligibility: EligibilityReport) -> list[BlockedCourse]:
        required = [entry for entry in eligibility.blocked if entry.course.type is CourseType.REQUIRED]
        required.sort(key=lambda entry: (entry.course.level, entry.course.code))
        return [
            BlockedCourse(
                code=entry.course.code,
                name=entry.course.name,
                level=entry.course.level,
                missing_prerequisites=entry.missing_prerequisites,
            )
            for entry in required[:MAX_BLOCKED_COURSES]
        ]

    @staticmethod
    def _progress(plan: StudyPlan, grades: dict[str, str | None]) -> Progress:
        completed_hours = sum(plan.by_code[code].credit_hours for code in grades)
        outstanding = [
            course
            for course in plan.courses
            if course.type is CourseType.REQUIRED and course.code not in grades
        ]
        return Progress(
            completed_hours=completed_hours,
            total_hours=plan.total_hours,
            remaining_required_courses=len(outstanding),
        )
