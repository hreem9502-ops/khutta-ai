"""Extracts text lines from an uploaded transcript PDF."""

import io
import unicodedata

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from app.errors import InvalidTranscriptError, UnreadableTranscriptError

PDF_SIGNATURE = b"%PDF-"
MAX_PAGES = 30


def extract_text_lines(data: bytes) -> list[str]:
    """Return the non-empty text lines of ``data`` in reading order.

    Raises:
        InvalidTranscriptError: ``data`` is not a readable PDF.
        UnreadableTranscriptError: the PDF has no text layer (for example a scan).
    """
    if not data.startswith(PDF_SIGNATURE):
        raise InvalidTranscriptError("File is not a PDF")

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = pdf.pages[:MAX_PAGES]
            texts = [page.extract_text(y_tolerance=8) or "" for page in pages]
    except (PdfminerException, ValueError) as error:
        raise InvalidTranscriptError("PDF could not be opened") from error

    lines = [
        unicodedata.normalize("NFKC", line).strip()
        for text in texts
        for line in text.splitlines()
        if line.strip()
    ]
    if not lines:
        raise UnreadableTranscriptError("PDF contains no extractable text")
    return lines
