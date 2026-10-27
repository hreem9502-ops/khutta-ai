"""Recommendation endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_recommendation_service
from app.models.suggestion import Recommendation, RecommendationRequest
from app.services.recommender import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=Recommendation)
async def create_recommendation(
    request: RecommendationRequest,
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
) -> Recommendation:
    """Recommend courses for the next term from a confirmed list of completed courses."""
    return await service.recommend(request)
