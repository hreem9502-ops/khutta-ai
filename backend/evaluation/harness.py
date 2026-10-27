"""Runs evaluation cases through the real services and scores the results."""

from dataclasses import dataclass

from app.config import get_settings
from app.models.student import ParsedTranscript
from app.models.suggestion import CompletedCourse, RecommendationRequest
from app.services.advisor_types import Advisor
from app.services.ai_advisor import GeminiAdvisor
from app.services.ai_transcript_reader import AITranscriptReader
from app.services.gemini_client import GeminiJsonClient
from app.services.plan_repository import PlanRepository
from app.services.plan_store import DirectoryPlanStore
from app.services.recommender import RecommendationService
from app.services.rule_advisor import RuleBasedAdvisor
from app.services.transcript_service import TranscriptService
from evaluation.audit import audit_recommendation
from evaluation.cases import EvaluationCase, ExpectedReading

GPA_TOLERANCE = 0.005


@dataclass(frozen=True)
class ReadingScore:
    """How well the transcript reader matched the expected reading."""

    correct: int
    predicted: int
    expected: int
    gpa_correct: bool | None

    @property
    def precision(self) -> float:
        return self.correct / self.predicted if self.predicted else 1.0

    @property
    def recall(self) -> float:
        return self.correct / self.expected if self.expected else 1.0


@dataclass(frozen=True)
class AdvisorAgreement:
    """Overlap between the recommended courses and an advisor's own picks."""

    overlap: int
    recommended: int
    advisor: int

    @property
    def precision(self) -> float:
        return self.overlap / self.recommended if self.recommended else 0.0

    @property
    def recall(self) -> float:
        return self.overlap / self.advisor if self.advisor else 0.0


@dataclass(frozen=True)
class CaseResult:
    case: EvaluationCase
    reader: str
    reading: ReadingScore
    recommended: list[str]
    total_hours: int
    max_hours: int
    source: str
    violations: list[str]
    agreement: AdvisorAgreement | None


def score_reading(parsed: ParsedTranscript, expected: ExpectedReading) -> ReadingScore:
    """A course counts as correct when it was found with the expected status."""
    truth = expected.statuses()
    found = {course.code: course.status.value for course in parsed.courses}
    correct = sum(1 for code, status in found.items() if truth.get(code) == status)
    gpa_correct = None
    if expected.gpa is not None:
        gpa_correct = parsed.gpa is not None and abs(parsed.gpa - expected.gpa) < GPA_TOLERANCE
    return ReadingScore(correct=correct, predicted=len(found), expected=len(truth), gpa_correct=gpa_correct)


class Harness:
    """Holds the services under test; build with :meth:`create`."""

    def __init__(self, plans: PlanRepository, transcripts: TranscriptService, recommender: RecommendationService):
        self.plans = plans
        self.transcripts = transcripts
        self.recommender = recommender

    @classmethod
    def create(cls, *, use_ai: bool) -> "Harness":
        """Wire the production services; AI is used only if requested and a key is configured."""
        settings = get_settings()
        plans = PlanRepository.from_store(DirectoryPlanStore(settings.plans_directory))
        client = None
        if use_ai and settings.ai_enabled:
            client = GeminiJsonClient(settings.gemini_api_keys, settings.gemini_model, settings.gemini_timeout_seconds)
        rules = RuleBasedAdvisor()
        primary: Advisor = GeminiAdvisor(client) if client else rules
        return cls(
            plans,
            TranscriptService(AITranscriptReader(client) if client else None),
            RecommendationService(plans, primary=primary, fallback=rules),
        )

    async def evaluate(self, case: EvaluationCase) -> CaseResult:
        """Score the reading, then recommend from the *expected* reading so the two are judged separately."""
        plan = self.plans.get(case.department)
        parsed = await self.transcripts.parse_lines(case.transcript, plan)
        grades = {course.code: course.grade for course in parsed.courses}

        request = RecommendationRequest(
            department=case.department,
            term=case.term,
            completed=[CompletedCourse(code=code, grade=grades.get(code)) for code in case.expected.passed],
            in_progress=case.expected.in_progress,
            gpa=case.expected.gpa,
        )
        recommendation = await self.recommender.recommend(request)
        recommended = [course.code for course in recommendation.courses]

        agreement = None
        if case.advisor_choice is not None:
            agreement = AdvisorAgreement(
                overlap=len(set(recommended) & set(case.advisor_choice)),
                recommended=len(recommended),
                advisor=len(case.advisor_choice),
            )

        return CaseResult(
            case=case,
            reader=parsed.reader.value,
            reading=score_reading(parsed, case.expected),
            recommended=recommended,
            total_hours=recommendation.total_hours,
            max_hours=recommendation.max_hours,
            source=recommendation.source.value,
            violations=audit_recommendation(
                plan,
                recommendation,
                passed=set(case.expected.passed),
                in_progress=set(case.expected.in_progress),
                term=case.term,
                gpa=case.expected.gpa,
            ),
            agreement=agreement,
        )
