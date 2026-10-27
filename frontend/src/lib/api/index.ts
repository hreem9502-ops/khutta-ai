import type {
  DepartmentSummary,
  ParsedTranscript,
  PlanImportResult,
  Recommendation,
  RecommendationRequest,
  StudyPlan,
} from "@/types";
import { apiUrl, request } from "./client";

export { ApiError } from "./client";

export function getDepartments(): Promise<DepartmentSummary[]> {
  return request("/departments");
}

export function getStudyPlan(department: string): Promise<StudyPlan> {
  return request(`/departments/${encodeURIComponent(department)}/plan`);
}

/** Direct link to a plan as an Excel workbook. */
export function studyPlanWorkbookUrl(department: string): string {
  return apiUrl(`/departments/${encodeURIComponent(department)}/plan.xlsx`);
}

export function parseTranscript(file: File, department: string): Promise<ParsedTranscript> {
  const body = new FormData();
  body.set("file", file);
  body.set("department", department);
  return request("/transcripts/parse", { method: "POST", body });
}

export function createRecommendation(payload: RecommendationRequest): Promise<Recommendation> {
  return request("/recommendations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/** Checks a plan workbook; with `publish`, also makes it live if it has no issues. */
export function importStudyPlan(file: File, token: string, publish: boolean): Promise<PlanImportResult> {
  const body = new FormData();
  body.set("file", file);
  return request(`/admin/plans?publish=${publish}`, {
    method: "POST",
    headers: { "X-Admin-Token": token },
    body,
  });
}
