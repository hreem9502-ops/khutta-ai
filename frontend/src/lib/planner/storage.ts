import { PLANNER_STORAGE_KEY } from "@/lib/constants";
import type { PlannerState } from "./state";

/** Reads the saved planner state; returns `null` if absent or unreadable. */
export function loadPlannerState(): Partial<PlannerState> | null {
  try {
    const raw = window.sessionStorage.getItem(PLANNER_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Partial<PlannerState>) : null;
  } catch {
    return null;
  }
}

export function savePlannerState(state: PlannerState): void {
  const { department, term, entries, detected, reader, gpa, recommendation } = state;
  try {
    window.sessionStorage.setItem(
      PLANNER_STORAGE_KEY,
      JSON.stringify({ department, term, entries, detected, reader, gpa, recommendation }),
    );
  } catch {
    // Storage can be unavailable (private mode, quota); the flow still works in memory.
  }
}
