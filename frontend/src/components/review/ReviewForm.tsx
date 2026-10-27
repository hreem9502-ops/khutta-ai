"use client";

import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { EmptyState } from "@/components/layout/EmptyState";
import { Button, ButtonLink, Field, Notice, TextInput } from "@/components/ui";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { usePlanner } from "@/hooks/usePlanner";
import { useStudyPlan } from "@/hooks/useStudyPlan";
import { useRouter } from "@/i18n/routing";
import { createRecommendation } from "@/lib/api";
import { buildRecommendationRequest } from "@/lib/planner/state";
import type { Course } from "@/types";
import { CourseRow } from "./CourseRow";

/** Groups required courses by level, in ascending order, and returns electives separately. */
function groupCourses(courses: Course[]) {
  const required = new Map<number, Course[]>();
  for (const course of courses) {
    if (course.type !== "required") continue;
    required.set(course.level, [...(required.get(course.level) ?? []), course]);
  }
  return {
    levels: [...required.entries()].sort(([a], [b]) => a - b),
    electives: courses.filter((course) => course.type === "elective"),
  };
}

/** Second step: the student confirms which plan courses they have passed or are taking. */
export function ReviewForm() {
  const t = useTranslations("Review");
  const router = useRouter();
  const describeError = useErrorMessage();
  const { state, hydrated, setCourseState, setGpa, setRecommendation } = usePlanner();
  const plan = useStudyPlan(state.department);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const groups = useMemo(() => groupCourses(plan.data?.courses ?? []), [plan.data]);

  if (!hydrated) return null;
  if (!state.department) return <EmptyState />;
  if (plan.error !== undefined) return <Notice tone="error">{describeError(plan.error)}</Notice>;
  if (!plan.data) return null;

  const entries = Object.values(state.entries);
  const passed = entries.filter((entry) => entry.state === "passed").length;
  const inProgress = entries.filter((entry) => entry.state === "in_progress").length;
  const gpaScale = plan.data.rules.gpa_scale;

  const handleGpaChange = (raw: string) => {
    const value = Number(raw);
    setGpa(raw === "" || Number.isNaN(value) || value < 0 || value > gpaScale ? null : value);
  };

  const handleGenerate = async () => {
    const payload = buildRecommendationRequest(state);
    if (!payload) return;
    setSubmitting(true);
    setError(null);
    try {
      setRecommendation(await createRecommendation(payload));
      router.push("/results");
    } catch (caught) {
      setError(describeError(caught));
      setSubmitting(false);
    }
  };

  const renderRow = (course: Course) => (
    <CourseRow
      key={course.code}
      course={course}
      entry={state.entries[course.code]}
      fromTranscript={state.detected.includes(course.code)}
      onChange={(next) => setCourseState(course.code, next)}
    />
  );

  return (
    <div className="space-y-10">
      {state.reader === "ai" && <Notice tone="warning">{t("aiRead")}</Notice>}

      <section className="grid gap-6 sm:grid-cols-2 sm:items-end">
        <div className="space-y-1 text-sm">
          <p className="font-medium text-ink">{t("detected", { count: state.detected.length })}</p>
          <p className="text-muted tabular">{t("summary", { passed, inProgress })}</p>
          {state.detected.length === 0 && <p className="text-muted">{t("noneDetected")}</p>}
        </div>
        <Field id="gpa" label={t("gpa")} hint={t("gpaHint")}>
          <TextInput
            id="gpa"
            type="number"
            inputMode="decimal"
            min={0}
            max={gpaScale}
            step={0.01}
            defaultValue={state.gpa ?? ""}
            onChange={(event) => handleGpaChange(event.target.value)}
            className="max-w-40 tabular"
          />
        </Field>
      </section>

      {groups.levels.map(([level, courses]) => (
        <section key={level} aria-labelledby={`level-${level}`}>
          <h2 id={`level-${level}`} className="border-b border-line-strong pb-2 font-semibold">
            {t("level", { level })}
          </h2>
          <ul className="divide-y divide-line">{courses.map(renderRow)}</ul>
        </section>
      ))}

      {groups.electives.length > 0 && (
        <section aria-labelledby="electives">
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line-strong pb-2">
            <h2 id="electives" className="font-semibold">
              {t("electives")}
            </h2>
            <p className="text-sm text-muted">{t("electivesHint", { hours: plan.data.elective_hours_required })}</p>
          </div>
          <ul className="divide-y divide-line">{groups.electives.map(renderRow)}</ul>
        </section>
      )}

      <div className="sticky bottom-0 -mx-4 space-y-3 border-t border-line bg-canvas px-4 py-4 sm:-mx-6 sm:px-6">
        {error && <Notice tone="error">{error}</Notice>}
        <div className="flex items-center justify-between gap-3">
          <ButtonLink href="/upload" variant="ghost">
            {t("back")}
          </ButtonLink>
          <Button size="lg" onClick={handleGenerate} loading={submitting}>
            {submitting ? t("generating") : t("generate")}
          </Button>
        </div>
      </div>
    </div>
  );
}
