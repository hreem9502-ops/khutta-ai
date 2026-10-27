"""Rule-based advisor: ranks eligible courses without any language model.

Used as the fallback when the AI advisor is unavailable, and as the source of top-up
courses when a selection falls below the minimum load.
"""

from app.constants import BOTTLENECK_UNLOCK_THRESHOLD
from app.models.common import LocalizedText
from app.models.course import Course, CourseType
from app.models.suggestion import Priority, RecommendationSource
from app.services.advisor_types import AdvisorContext, Choice, Selection


def arabic_count(count: int, one: str, two: str, few: str, many: str) -> str:
    """Format ``count`` with the Arabic noun form it requires (genitive case)."""
    if count == 1:
        return one
    if count == 2:
        return two
    return f"{count} {few}" if count <= 10 else f"{count} {many}"


def rank_courses(context: AdvisorContext) -> list[Course]:
    """Order eligible courses: required first, lower levels first, bottlenecks first."""
    return sorted(
        context.eligible,
        key=lambda course: (
            course.type is CourseType.ELECTIVE,
            course.level,
            -context.unlock_count(course.code),
            course.code,
        ),
    )


def lowest_required_level(context: AdvisorContext) -> int:
    """The lowest plan level that still has an eligible required course (0 if none)."""
    return min(
        (course.level for course in context.eligible if course.type is CourseType.REQUIRED),
        default=0,
    )


def describe_course(context: AdvisorContext, course: Course) -> Choice:
    """Build a templated choice (priority and bilingual reason) for ``course``."""
    unlocks = context.unlock_count(course.code)
    is_bottleneck = unlocks >= BOTTLENECK_UNLOCK_THRESHOLD

    if course.type is CourseType.ELECTIVE:
        return Choice(
            code=course.code,
            priority=Priority.LOW,
            reason=LocalizedText(
                ar="مادة اختيارية تكمل الساعات الاختيارية المطلوبة في خطتك.",
                en="Elective that counts toward your required elective hours.",
            ),
        )

    is_lowest = course.level == lowest_required_level(context)
    return Choice(
        code=course.code,
        priority=Priority.HIGH if is_lowest or is_bottleneck else Priority.MEDIUM,
        reason=_required_reason(course, unlocks, is_bottleneck, is_lowest),
    )


def _required_reason(course: Course, unlocks: int, is_bottleneck: bool, is_lowest: bool) -> LocalizedText:
    if is_lowest:
        ar = f"من أقدم مواد خطتك المتبقية (المستوى {course.level})"
        en = f"One of your earliest outstanding courses (Level {course.level})"
    else:
        ar = f"مادة من المستوى {course.level} في خطتك"
        en = f"Level {course.level} course in your plan"
    if is_bottleneck:
        later = arabic_count(unlocks, "مادة لاحقة", "مادتين لاحقتين", "مواد لاحقة", "مادة لاحقة")
        ar += f"، وهي متطلب سابق لـ {later}"
        en += f", and a prerequisite for {unlocks} later courses"
    return LocalizedText(ar=ar + ".", en=en + ".")


class RuleBasedAdvisor:
    """Greedy selection up to the target load, in :func:`rank_courses` order."""

    source = RecommendationSource.RULES

    async def advise(self, context: AdvisorContext) -> Selection:
        chosen: list[Course] = []
        total = 0
        elective_budget = context.elective_hours_remaining

        for course in rank_courses(context):
            if total + course.credit_hours > context.target_hours:
                continue
            if course.type is CourseType.ELECTIVE:
                if course.credit_hours > elective_budget:
                    continue
                elective_budget -= course.credit_hours
            chosen.append(course)
            total += course.credit_hours

        choices = [describe_course(context, course) for course in chosen]
        courses_ar = arabic_count(len(choices), "مادة واحدة", "مادتين", "مواد", "مادة")
        hours_ar = arabic_count(total, "ساعة واحدة", "ساعتين", "ساعات", "ساعة")
        summary = LocalizedText(
            ar=f"اشتمل الجدول على {courses_ar} بمجموع {hours_ar}، مرتبة بالمستوى ثم بأهمية المادة كمتطلب لمواد أخرى.",
            en=(
                f"Selected {len(choices)} courses ({total} credit hours), ordered by level "
                "and then by how many later courses depend on each."
            ),
        )
        return Selection(choices=choices, summary=summary)
