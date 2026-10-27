import { useContext } from "react";
import { PlannerContext, type PlannerContextValue } from "./planner-context";

/** Access the shared planner state. Must be used inside `PlannerProvider`. */
export function usePlanner(): PlannerContextValue {
  const context = useContext(PlannerContext);
  if (!context) throw new Error("usePlanner must be used within PlannerProvider");
  return context;
}
