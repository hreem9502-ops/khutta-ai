import { createContext } from "react";
import type { CourseState, Recommendation, Term, TranscriptCourse, TranscriptReader } from "@/types";
import type { PlannerState } from "@/lib/planner/state";

export interface PlannerContextValue {
  state: PlannerState;
  /** False until the saved session state has been read; guards redirects on page load. */
  hydrated: boolean;
  start: (input: {
    department: string;
    term: Term;
    courses: TranscriptCourse[];
    gpa: number | null;
    reader: TranscriptReader | null;
  }) => void;
  setCourseState: (code: string, state: CourseState) => void;
  setGpa: (gpa: number | null) => void;
  setRecommendation: (recommendation: Recommendation) => void;
  reset: () => void;
}

export const PlannerContext = createContext<PlannerContextValue | null>(null);
