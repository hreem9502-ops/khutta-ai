"""FastAPI dependency providers. Services are built once and shared."""

from functools import lru_cache

from app.config import get_settings
from app.services.advisor_types import Advisor
from app.services.ai_advisor import GeminiAdvisor
from app.services.ai_transcript_reader import AITranscriptReader
from app.services.gemini_client import GeminiJsonClient
from app.services.plan_repository import PlanRepository
from app.services.plan_store import DirectoryPlanStore, RedisPlanStore
from app.services.recommender import RecommendationService
from app.services.rule_advisor import RuleBasedAdvisor
from app.services.transcript_service import TranscriptService


@lru_cache
def get_plan_repository() -> PlanRepository:
    """Plans from Redis when configured (hosted), otherwise from the local plans directory."""
    settings = get_settings()
    bundled = DirectoryPlanStore(settings.plans_directory)
    if not settings.redis_enabled:
        return PlanRepository.from_store(bundled)
    store = RedisPlanStore(settings.kv_rest_api_url, settings.kv_rest_api_token, seed=bundled)
    return PlanRepository.from_store(store, refresh_seconds=settings.plan_cache_seconds)


@lru_cache
def get_ai_client() -> GeminiJsonClient | None:
    """The shared Gemini client, or ``None`` when no API key is configured."""
    settings = get_settings()
    if not settings.ai_enabled:
        return None
    return GeminiJsonClient(
        api_key=settings.gemini_api_keys,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
    )


@lru_cache
def get_recommendation_service() -> RecommendationService:
    rules = RuleBasedAdvisor()
    client = get_ai_client()
    primary: Advisor = GeminiAdvisor(client) if client else rules
    return RecommendationService(get_plan_repository(), primary=primary, fallback=rules)


@lru_cache
def get_transcript_service() -> TranscriptService:
    client = get_ai_client()
    return TranscriptService(AITranscriptReader(client) if client else None)
