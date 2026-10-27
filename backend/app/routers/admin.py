"""Staff-only endpoints for maintaining study plans."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.dependencies import get_plan_repository
from app.errors import PlanStorageUnavailableError
from app.models.admin import PlanImportResult
from app.security import require_admin
from app.services.plan_repository import PlanRepository
from app.services.plan_spreadsheet import read_plan_workbook, summarize_plan
from app.services.plan_store import PlanStoreError
from app.uploads import read_upload

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/plans", response_model=PlanImportResult)
async def import_plan(
    file: Annotated[UploadFile, File(description="Study plan workbook (.xlsx)")],
    plans: Annotated[PlanRepository, Depends(get_plan_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
    publish: Annotated[bool, Query(description="Save the plan if it has no issues")] = False,
) -> PlanImportResult:
    """Check a plan workbook and, when ``publish`` is true and it is valid, make it live.

    Publishing replaces any existing plan with the same department code.
    """
    data = await read_upload(file, settings.max_upload_bytes)
    plan, issues = await run_in_threadpool(read_plan_workbook, data)
    if plan is not None and publish:
        try:
            plans.save(plan)
        except (OSError, PlanStoreError) as error:
            raise PlanStorageUnavailableError(f"Plans cannot be saved: {error}") from error
    return PlanImportResult(
        summary=summarize_plan(plan) if plan else None,
        issues=issues,
        published=plan is not None and publish,
    )
