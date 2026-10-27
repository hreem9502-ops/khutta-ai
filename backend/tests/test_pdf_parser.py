import pytest

from app.errors import InvalidTranscriptError, UnreadableTranscriptError
from app.services.pdf_parser import extract_text_lines
from app.services.transcript_analyzer import analyze_transcript


def test_extracts_lines_in_reading_order(make_pdf):
    data = make_pdf(["Transcript", "CS 101 Introduction to Computing 3 A"])

    assert extract_text_lines(data) == ["Transcript", "CS 101 Introduction to Computing 3 A"]


def test_extracted_pdf_text_feeds_the_analyzer(make_pdf, cs_plan):
    data = make_pdf(
        [
            "Cumulative GPA: 3.10",
            "CS 101 Introduction to Computing 3 A 4.00",
            "CS 102 Programming 1 4 B+ 3.50",
        ]
    )

    result = analyze_transcript(extract_text_lines(data), cs_plan)

    assert [(course.code, course.grade) for course in result.courses] == [("CS 101", "A"), ("CS 102", "B+")]
    assert result.gpa == 3.10


@pytest.mark.parametrize("payload", [b"", b"not a pdf", b"%PDF-1.7 broken"])
def test_rejects_data_that_is_not_a_readable_pdf(payload):
    with pytest.raises(InvalidTranscriptError):
        extract_text_lines(payload)


def test_pdf_without_a_text_layer_is_reported_as_unreadable(blank_pdf):
    with pytest.raises(UnreadableTranscriptError):
        extract_text_lines(blank_pdf)
