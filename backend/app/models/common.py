"""Small value types shared across the API schemas."""

import re

from pydantic import BaseModel

_CODE_PARTS = re.compile(r"^([A-Za-z\u0621-\u064A]+)[\s\-]*(\d+)$")
_REVERSED_CODE_PARTS = re.compile(r"^(\d+)[\s\-]*([A-Za-z\u0621-\u064A]+)$")
_ARABIC_MARKS = re.compile(r"[ً-ْـ]")
_ARABIC_LETTER_FORMS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"})


class LocalizedText(BaseModel):
    """A string available in every supported UI language."""

    ar: str
    en: str


def normalize_course_code(raw: str) -> str:
    """Return the canonical ``"CS 101"`` form of a course code.

    ``cs101``, ``CS-101`` and ``cs 101`` all normalise to ``"CS 101"``. Reversed RTL codes
    such as ``"111 شبكا"`` also normalise to ``"شبكا 111"``. Input that does not look like
    a course code is returned stripped and upper-cased so that callers can reject it by
    looking it up in the study plan.
    """
    cleaned = _ARABIC_MARKS.sub("", raw.strip()).translate(_ARABIC_LETTER_FORMS)
    match = _CODE_PARTS.match(cleaned)
    if match:
        prefix, number = match.groups()
        return f"{prefix.upper()} {number}"
    reversed_match = _REVERSED_CODE_PARTS.match(cleaned)
    if reversed_match:
        number, prefix = reversed_match.groups()
        return f"{prefix.upper()} {number}"
    return cleaned.upper()
