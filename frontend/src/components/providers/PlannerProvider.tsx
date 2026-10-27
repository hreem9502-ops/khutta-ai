"use client";

import { useCallback, useEffect, useMemo, useReducer, type ReactNode } from "react";
import { PlannerContext, type PlannerContextValue } from "@/hooks/planner-context";
import { loadPlannerState, savePlannerState } from "@/lib/planner/storage";
import { INITIAL_PLANNER_STATE, plannerReducer } from "@/lib/planner/state";

/** Holds the planner state for the browser session and keeps it in sessionStorage. */
export function PlannerProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(plannerReducer, INITIAL_PLANNER_STATE);

  useEffect(() => {
    dispatch({ type: "hydrate", saved: loadPlannerState() });
  }, []);

  useEffect(() => {
    if (state.hydrated) savePlannerState(state);
  }, [state]);

  const start = useCallback<PlannerContextValue["start"]>(
    (input) => dispatch({ type: "start", ...input }),
    [],
  );
  const setCourseState = useCallback<PlannerContextValue["setCourseState"]>(
    (code, courseState) => dispatch({ type: "setCourseState", code, state: courseState }),
    [],
  );
  const setGpa = useCallback<PlannerContextValue["setGpa"]>(
    (gpa) => dispatch({ type: "setGpa", gpa }),
    [],
  );
  const setRecommendation = useCallback<PlannerContextValue["setRecommendation"]>(
    (recommendation) => dispatch({ type: "setRecommendation", recommendation }),
    [],
  );
  const reset = useCallback(() => dispatch({ type: "reset" }), []);

  const value = useMemo<PlannerContextValue>(
    () => ({ state, hydrated: state.hydrated, start, setCourseState, setGpa, setRecommendation, reset }),
    [state, start, setCourseState, setGpa, setRecommendation, reset],
  );

  return <PlannerContext.Provider value={value}>{children}</PlannerContext.Provider>;
}
