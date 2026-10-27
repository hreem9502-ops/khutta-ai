import { useCallback } from "react";
import { getStudyPlan } from "@/lib/api";
import { useApiResource } from "./useApiResource";

/** Loads a department's study plan; pass `null` until a department is chosen. */
export function useStudyPlan(department: string | null) {
  const load = useCallback(() => getStudyPlan(department ?? ""), [department]);
  return useApiResource(load, department);
}
