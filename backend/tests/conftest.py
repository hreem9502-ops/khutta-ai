"""Shared fixtures."""

import io
from collections.abc import Callable
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.config import get_settings
from app.models.course import StudyPlan
from app.services.plan_repository import PlanRepository
from app.services.plan_store import DirectoryPlanStore


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def repository() -> PlanRepository:
    return PlanRepository.from_store(DirectoryPlanStore(get_settings().plans_directory))


@pytest.fixture(scope="session")
def cs_plan(repository: PlanRepository) -> StudyPlan:
    return repository.get("cs")


@pytest.fixture
def make_pdf() -> Callable[[list[str]], bytes]:
    """Build a text PDF with one line of text per entry (Latin text only)."""

    def build(lines: list[str]) -> bytes:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        y = 800
        for line in lines:
            pdf.drawString(40, y, line)
            y -= 16
        pdf.save()
        return buffer.getvalue()

    return build


@pytest.fixture
def blank_pdf() -> bytes:
    """A valid PDF that has no text layer."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.rect(50, 50, 100, 100)
    pdf.save()
    return buffer.getvalue()


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "app" / "data" / "plans"


def clear_dependency_caches() -> None:
    """Forget cached settings and services so environment overrides take effect."""
    from app import dependencies

    get_settings.cache_clear()
    for provider in (
        dependencies.get_plan_repository,
        dependencies.get_ai_client,
        dependencies.get_recommendation_service,
        dependencies.get_transcript_service,
    ):
        provider.cache_clear()
