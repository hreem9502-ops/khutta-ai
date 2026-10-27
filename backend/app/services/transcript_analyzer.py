"""Turns raw transcript text into the plan courses a student has taken.

Parsing is deliberately conservative: only course codes that exist in the department's
study plan are recognised, and a grade is accepted only when it sits at the end of the
line (optionally followed by numeric point columns). When unsure, a course is reported
as in progress rather than passed; the student confirms the result before anything is
recommended.
"""

import re
from collections.abc import Iterable

from app.constants import (
    ALL_GRADE_TOKENS,
    COURSE_CODE_PATTERN,
    FAILING_GRADES,
    GPA_LABEL_PATTERN,
    GPA_VALUE_PATTERN,
    PASSING_GRADES,
    REVERSED_COURSE_CODE_PATTERN,
)
from app.models.common import normalize_course_code
from app.models.course import StudyPlan
from app.models.student import CourseStatus, ParsedTranscript, TranscriptCourse

_COURSE_CODE = re.compile(rf"(?<![A-Za-z\dء-ي])({COURSE_CODE_PATTERN})(?![A-Za-z\dء-ي])")
_REVERSED_COURSE_CODE = re.compile(rf"(?<![A-Za-z\dء-ي])({REVERSED_COURSE_CODE_PATTERN})(?![A-Za-z\dء-ي])")
_GPA = re.compile(rf"{GPA_LABEL_PATTERN}\D{{0,30}}?{GPA_VALUE_PATTERN}", re.IGNORECASE)
_GPA_REVERSED = re.compile(rf"{GPA_VALUE_PATTERN}\D{{0,30}}?{GPA_LABEL_PATTERN}", re.IGNORECASE)
_NUMBER = re.compile(r"^\d+(?:\.\d+)?$")
_ARABIC_MARKS = re.compile(r"[ً-ْـ]")
_ARABIC_LETTER_FORMS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"})

# Higher wins when a course appears on several lines (for example a failed first attempt
# followed by a passing retake).
_STATUS_PRECEDENCE = {
    CourseStatus.PASSED: 3,
    CourseStatus.IN_PROGRESS: 2,
    CourseStatus.FAILED: 1,
}


def normalize_token(token: str) -> str:
    """Upper-case Latin text and strip Arabic diacritics and alef variants."""
    return _ARABIC_MARKS.sub("", token.strip()).translate(_ARABIC_LETTER_FORMS).upper()


def analyze_transcript(lines: Iterable[str], plan: StudyPlan) -> ParsedTranscript:
    """Match transcript ``lines`` against ``plan`` and return the recognised courses."""
    lines = list(lines)
    attempts = [course for line in lines if (course := _read_course_line(line, plan)) is not None]
    return ParsedTranscript(
        department=plan.code,
        courses=merge_attempts(attempts, plan),
        gpa=_read_gpa(lines, plan),
    )


def merge_attempts(attempts: Iterable[TranscriptCourse], plan: StudyPlan) -> list[TranscriptCourse]:
    """Keep the strongest attempt per course (passed > in progress > failed), in plan order."""
    best: dict[str, TranscriptCourse] = {}
    for course in attempts:
        current = best.get(course.code)
        if current is None or _STATUS_PRECEDENCE[course.status] > _STATUS_PRECEDENCE[current.status]:
            best[course.code] = course
    return sorted(best.values(), key=lambda course: plan.by_code[course.code].level)


def course_from_grade(code: str, raw_grade: str | None) -> TranscriptCourse:
    """Build a transcript entry, keeping the grade only if it is a recognised grade token."""
    grade = normalize_token(raw_grade) if raw_grade else None
    if grade not in ALL_GRADE_TOKENS:
        grade = None
    return TranscriptCourse(code=code, grade=grade, status=status_for_grade(grade))


def _read_course_line(line: str, plan: StudyPlan) -> TranscriptCourse | None:
    """Return the course described by ``line`` or ``None`` if it names no plan course."""
    for match in (*_COURSE_CODE.finditer(line), *_REVERSED_COURSE_CODE.finditer(line)):
        code = _resolve_plan_code(match.group(1), plan)
        if code is None:
            continue
        grade = _find_grade(line[match.end() :].split())
        if grade is None:
            grade = _find_grade(list(reversed(line[: match.start()].split())))
        return TranscriptCourse(code=code, grade=grade, status=status_for_grade(grade))
    return None


def _resolve_plan_code(raw_code: str, plan: StudyPlan) -> str | None:
    """Match ``raw_code`` against ``plan``, including visual-order reversed Arabic prefixes."""
    code = normalize_course_code(raw_code)
    if code in plan.by_code:
        return code
    parts = code.split(" ", 1)
    if len(parts) == 2:
        reversed_prefix_code = f"{parts[0][::-1]} {parts[1]}"
        if reversed_prefix_code in plan.by_code:
            return reversed_prefix_code
    return None


def status_for_grade(grade: str | None) -> CourseStatus:
    """Passed, failed or (when there is no recognised grade) in progress."""
    if grade in PASSING_GRADES:
        return CourseStatus.PASSED
    if grade in FAILING_GRADES:
        return CourseStatus.FAILED
    return CourseStatus.IN_PROGRESS


def _find_grade(tokens: list[str]) -> str | None:
    """Find the grade in the tokens that follow a course code.

    The search starts after the first number (the credit-hours column) so that letters in
    the course title, such as ``Programming in C``, are never mistaken for a grade. The
    grade must be followed only by numbers (grade points).
    """
    normalized = [normalize_token(token) for token in tokens]
    start = next((i + 1 for i, token in enumerate(normalized) if _NUMBER.match(token)), len(normalized))

    candidates: list[tuple[int, str]] = []  # (index just past the grade, grade)
    index = start
    while index < len(normalized):
        pair = " ".join(normalized[index : index + 2])
        if pair in ALL_GRADE_TOKENS:
            candidates.append((index + 2, pair))
            index += 2
            continue
        if normalized[index] in ALL_GRADE_TOKENS:
            candidates.append((index + 1, normalized[index]))
        index += 1

    for end, grade in reversed(candidates):
        if all(_NUMBER.match(token) for token in normalized[end:]):
            return grade
    return None


def _read_gpa(lines: list[str], plan: StudyPlan) -> float | None:
    """Return the cumulative GPA stated in the transcript, if it is plausible."""
    for line in lines:
        for pattern in (_GPA, _GPA_REVERSED):
            match = pattern.search(line)
            if match:
                value = float(match.group(1))
                if 0 < value <= plan.rules.gpa_scale:
                    return value
    return None
