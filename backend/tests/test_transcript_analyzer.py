import pytest

from app.models.student import CourseStatus
from app.services.transcript_analyzer import analyze_transcript, normalize_token


def parse(cs_plan, *lines: str):
    return analyze_transcript(lines, cs_plan)


def by_code(result):
    return {course.code: course for course in result.courses}


def test_reads_code_hours_and_grade_columns(cs_plan):
    result = parse(cs_plan, "CS 101 Introduction to Computing 3 A+ 4.00 12.00")

    course = by_code(result)["CS 101"]
    assert course.grade == "A+"
    assert course.status is CourseStatus.PASSED


@pytest.mark.parametrize("written", ["CS101", "cs101", "CS-101", "CS 101"])
def test_code_spelling_variants_are_normalised(cs_plan, written):
    result = parse(cs_plan, f"{written} Introduction to Computing 3 B")

    assert list(by_code(result)) == ["CS 101"]


def test_ignores_codes_that_are_not_in_the_plan(cs_plan):
    result = parse(cs_plan, "PHYS 101 General Physics 3 A", "CS 101 Introduction to Computing 3 B")

    assert list(by_code(result)) == ["CS 101"]


def test_letter_in_course_title_is_not_read_as_a_grade(cs_plan):
    # No grade yet: "C" belongs to the title, so the course must not count as passed.
    result = parse(cs_plan, "CS 102 Programming in C 4")

    assert by_code(result)["CS 102"].status is CourseStatus.IN_PROGRESS
    assert by_code(result)["CS 102"].grade is None


def test_title_containing_a_number_does_not_hide_the_grade(cs_plan):
    result = parse(cs_plan, "CS 102 Programming 1 4 B+ 3.50 14.00")

    assert by_code(result)["CS 102"].grade == "B+"


def test_failing_and_in_progress_grades(cs_plan):
    result = parse(
        cs_plan,
        "MATH 101 Calculus 3 F 0.00 0.00",
        "ENG 101 English 1 3 IP",
    )

    assert by_code(result)["MATH 101"].status is CourseStatus.FAILED
    assert by_code(result)["ENG 101"].status is CourseStatus.IN_PROGRESS


def test_a_passing_retake_wins_over_an_earlier_failure(cs_plan):
    result = parse(
        cs_plan,
        "MATH 101 Calculus 3 F 0.00",
        "MATH 101 Calculus 3 C+ 2.50",
    )

    assert by_code(result)["MATH 101"].status is CourseStatus.PASSED
    assert by_code(result)["MATH 101"].grade == "C+"


def test_arabic_grade_words_including_multiword_grades(cs_plan):
    result = parse(
        cs_plan,
        "CS 101 3 جيد جداً",
        "ENG 101 3 ممتاز",
        "ISL 101 2 راسب",
    )

    assert by_code(result)["CS 101"].status is CourseStatus.PASSED
    assert by_code(result)["ENG 101"].status is CourseStatus.PASSED
    assert by_code(result)["ISL 101"].status is CourseStatus.FAILED


def test_courses_are_returned_in_plan_level_order(cs_plan):
    result = parse(cs_plan, "CS 201 Programming 2 4 B", "CS 101 Introduction 3 A", "CS 301 Data Structures 3 B")

    assert [course.code for course in result.courses] == ["CS 101", "CS 201", "CS 301"]


def test_no_recognised_courses_gives_an_empty_result(cs_plan):
    result = parse(cs_plan, "Student Transcript", "Page 1 of 1")

    assert result.courses == []


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Cumulative GPA: 3.42", 3.42),
        ("GPA 2.9", 2.9),
        ("المعدل التراكمي 3.75", 3.75),
    ],
)
def test_reads_the_stated_gpa(cs_plan, line, expected):
    assert parse(cs_plan, line).gpa == expected


def test_gpa_outside_the_plan_scale_is_ignored(cs_plan):
    assert parse(cs_plan, "GPA 4.9").gpa is None


def test_normalize_token_strips_arabic_marks_and_uppercases():
    assert normalize_token("جداً") == "جدا"
    assert normalize_token("b+") == "B+"
