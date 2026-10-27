"""Department and study plan endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_plan_repository
from app.models.course import DepartmentSummary, StudyPlan
from app.services.plan_repository import PlanRepository
from app.services.plan_spreadsheet import export_plan_workbook

router = APIRouter(prefix="/departments", tags=["departments"])

Plans = Annotated[PlanRepository, Depends(get_plan_repository)]


@router.get("", response_model=list[DepartmentSummary])
def list_departments(plans: Plans) -> list[DepartmentSummary]:
    """List the departments that have a study plan."""
    return plans.list_departments()


@router.get("/{code}/plan", response_model=StudyPlan)
def get_study_plan(code: str, plans: Plans) -> StudyPlan:
    """Return the full study plan for a department."""
    return plans.get(code)


XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/{code}/plan.xlsx", response_class=Response)
def download_study_plan(code: str, plans: Plans) -> Response:
    """Download a plan as an Excel workbook; staff edit it and upload it back through the admin import."""
    plan = plans.get(code)
    return Response(
        content=export_plan_workbook(plan),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{plan.code}-study-plan.xlsx"'},
    )
