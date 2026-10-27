"""Evaluation case format and loading."""

from pathlib import Path

from pydantic import BaseModel

from app.models.course import Term

CASES_DIRECTORY = Path(__file__).resolve().parent / "cases"


class ExpectedReading(BaseModel):
    """The correct reading of the transcript, as confirmed by a person."""

    passed: list[str] = []
    failed: list[str] = []
    in_progress: list[str] = []
    gpa: float | None = None

    def statuses(self) -> dict[str, str]:
        return {
            **{code: "failed" for code in self.failed},
            **{code: "in_progress" for code in self.in_progress},
            **{code: "passed" for code in self.passed},
        }


class EvaluationCase(BaseModel):
    """One student: transcript text, the right reading, and optionally an advisor's picks."""

    name: str
    description: str
    department: str
    term: Term
    transcript: list[str]
    expected: ExpectedReading
    advisor_choice: list[str] | None = None
    verified_by: str | None = None
    tags: list[str] = []
    note: str | None = None


def load_cases(directory: Path = CASES_DIRECTORY) -> list[EvaluationCase]:
    """Load every ``*.json`` case in ``directory``, sorted by file name."""
    return [
        EvaluationCase.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]
