/** Types mirroring the backend API schemas (see backend/app/models). */

export type Locale = "ar" | "en";

export interface LocalizedText {
  ar: string;
  en: string;
}

export type Term = "fall" | "spring";
export type CourseType = "required" | "elective";
export type CourseCategory = "theoretical" | "practical" | "mixed";
export type Priority = "high" | "medium" | "low";
export type RecommendationSource = "ai" | "rules";

export interface Course {
  code: string;
  name: LocalizedText;
  credit_hours: number;
  level: number;
  type: CourseType;
  category: CourseCategory;
  prerequisites: string[];
  corequisites: string[];
  terms: Term[];
}

export interface DepartmentSummary {
  code: string;
  name: LocalizedText;
  total_hours: number;
}

export interface CreditRules {
  gpa_scale: number;
  min_hours: number;
  default_max_hours: number;
}

export interface StudyPlan extends DepartmentSummary {
  elective_hours_required: number;
  rules: CreditRules;
  courses: Course[];
}

/** What a transcript line says about a course. */
export type TranscriptStatus = "passed" | "failed" | "in_progress";

export interface TranscriptCourse {
  code: string;
  grade: string | null;
  status: TranscriptStatus;
}

export type TranscriptReader = "rules" | "ai";

export interface ParsedTranscript {
  department: string;
  courses: TranscriptCourse[];
  gpa: number | null;
  reader: TranscriptReader;
}

export interface CompletedCourse {
  code: string;
  grade: string | null;
}

export interface RecommendationRequest {
  department: string;
  term: Term;
  completed: CompletedCourse[];
  in_progress: string[];
  gpa: number | null;
}

export interface RecommendedCourse {
  code: string;
  name: LocalizedText;
  credit_hours: number;
  level: number;
  type: CourseType;
  category: CourseCategory;
  priority: Priority;
  reason: LocalizedText;
}

export interface BlockedCourse {
  code: string;
  name: LocalizedText;
  level: number;
  missing_prerequisites: string[];
}

export interface Progress {
  completed_hours: number;
  total_hours: number;
  remaining_required_courses: number;
}

export interface Recommendation {
  courses: RecommendedCourse[];
  total_hours: number;
  min_hours: number;
  max_hours: number;
  summary: LocalizedText;
  warnings: LocalizedText[];
  blocked: BlockedCourse[];
  progress: Progress;
  source: RecommendationSource;
}

export type PlanIssueCode =
  | "invalid_file"
  | "missing_sheet"
  | "missing_column"
  | "missing_value"
  | "invalid_number"
  | "invalid_choice"
  | "invalid_department_code"
  | "duplicate_course"
  | "unknown_course"
  | "self_reference"
  | "prerequisite_cycle"
  | "invalid_rules";

export interface PlanIssue {
  code: PlanIssueCode;
  sheet: string | null;
  row: number | null;
  field: string | null;
  value: string | null;
}

export interface PlanImportSummary {
  code: string;
  name: LocalizedText;
  total_hours: number;
  course_count: number;
  level_count: number;
  elective_count: number;
}

export interface PlanImportResult {
  summary: PlanImportSummary | null;
  issues: PlanIssue[];
  published: boolean;
}

/** The student's standing in a single course, as confirmed on the review screen. */
export type CourseState = "passed" | "in_progress" | "none";

export interface CourseEntry {
  state: CourseState;
  grade: string | null;
}
