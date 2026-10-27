import type {
  CourseEntry,
  CourseState,
  Recommendation,
  RecommendationRequest,
  Term,
  TranscriptCourse,
  TranscriptReader,
} from "@/types";

/** Everything the student has told us so far, carried across the upload, review and results pages. */
export interface PlannerState {
  department: string | null;
  term: Term | null;
  /** Courses the student has an opinion on, keyed by course code. */
  entries: Record<string, CourseEntry>;
  /** Codes the transcript parser found, so the review screen can mark them. */
  detected: string[];
  /** Which reader produced `detected`; `null` when courses were entered manually. */
  reader: TranscriptReader | null;
  gpa: number | null;
  recommendation: Recommendation | null;
  /** False until the saved session state has been read; never persisted. */
  hydrated: boolean;
}

export const INITIAL_PLANNER_STATE: PlannerState = {
  department: null,
  term: null,
  entries: {},
  detected: [],
  reader: null,
  gpa: null,
  recommendation: null,
  hydrated: false,
};

export type PlannerAction =
  | { type: "hydrate"; saved: Partial<PlannerState> | null }
  | {
      type: "start";
      department: string;
      term: Term;
      courses: TranscriptCourse[];
      gpa: number | null;
      reader: TranscriptReader | null;
    }
  | { type: "setCourseState"; code: string; state: CourseState }
  | { type: "setGpa"; gpa: number | null }
  | { type: "setRecommendation"; recommendation: Recommendation }
  | { type: "reset" };

/** A parsed transcript line becomes a review entry; failed attempts count as not completed. */
function entryFromTranscript(course: TranscriptCourse): CourseEntry {
  const state: CourseState =
    course.status === "passed" ? "passed" : course.status === "in_progress" ? "in_progress" : "none";
  return { state, grade: course.grade };
}

export function plannerReducer(state: PlannerState, action: PlannerAction): PlannerState {
  switch (action.type) {
    case "hydrate":
      return { ...INITIAL_PLANNER_STATE, ...action.saved, hydrated: true };
    case "start":
      return {
        hydrated: true,
        department: action.department,
        term: action.term,
        entries: Object.fromEntries(
          action.courses.map((course) => [course.code, entryFromTranscript(course)]),
        ),
        detected: action.courses.map((course) => course.code),
        reader: action.reader,
        gpa: action.gpa,
        recommendation: null,
      };
    case "setCourseState": {
      const previous = state.entries[action.code];
      return {
        ...state,
        entries: {
          ...state.entries,
          [action.code]: { state: action.state, grade: previous?.grade ?? null },
        },
        recommendation: null,
      };
    }
    case "setGpa":
      return { ...state, gpa: action.gpa, recommendation: null };
    case "setRecommendation":
      return { ...state, recommendation: action.recommendation };
    case "reset":
      return { ...INITIAL_PLANNER_STATE, hydrated: true };
  }
}

/** Builds the API payload from confirmed state, or `null` if the flow has not been started. */
export function buildRecommendationRequest(state: PlannerState): RecommendationRequest | null {
  if (!state.department || !state.term) return null;

  const entries = Object.entries(state.entries);
  return {
    department: state.department,
    term: state.term,
    completed: entries
      .filter(([, entry]) => entry.state === "passed")
      .map(([code, entry]) => ({ code, grade: entry.grade })),
    in_progress: entries.filter(([, entry]) => entry.state === "in_progress").map(([code]) => code),
    gpa: state.gpa,
  };
}
