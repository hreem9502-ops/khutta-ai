"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { Field, Notice, Select } from "@/components/ui";
import { useDepartments } from "@/hooks/useDepartments";
import { useErrorMessage } from "@/hooks/useErrorMessage";
import { useStudyPlan } from "@/hooks/useStudyPlan";
import { localize } from "@/lib/utils";
import type { Course } from "@/types";

function CourseTable({ courses, caption }: { courses: Course[]; caption: string }) {
  const t = useTranslations("Plan");
  const tc = useTranslations("Common");
  const locale = useLocale();

  return (
    <table className="w-full text-start">
      <caption className="border-b border-line-strong pb-2 text-start font-semibold">{caption}</caption>
      <thead className="sr-only">
        <tr>
          <th>{t("code")}</th>
          <th>{t("course")}</th>
          <th>{t("hoursHeading")}</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {courses.map((course) => (
          <tr key={course.code} className="align-top">
            <td className="w-28 py-3 pe-4 text-sm font-medium text-brand" dir="auto">
              {course.code}
            </td>
            <td className="py-3 pe-4">
              <p className="font-medium">{localize(course.name, locale)}</p>
              <p className="text-sm text-muted" dir="auto">
                {course.prerequisites.length > 0
                  ? t("requires", { codes: course.prerequisites.join(", ") })
                  : t("noRequirements")}
              </p>
            </td>
            <td className="w-20 py-3 text-end text-sm text-muted tabular">
              {tc("hours", { hours: course.credit_hours })}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Browsable study plan for any department, grouped by level. */
export function PlanViewer() {
  const t = useTranslations("Plan");
  const locale = useLocale();
  const describeError = useErrorMessage();
  const departments = useDepartments();
  const [chosen, setChosen] = useState<string | null>(null);

  const department = chosen ?? departments.data?.[0]?.code ?? null;
  const plan = useStudyPlan(department);

  const groups = useMemo(() => {
    const courses = plan.data?.courses ?? [];
    const levels = new Map<number, Course[]>();
    for (const course of courses.filter((item) => item.type === "required")) {
      levels.set(course.level, [...(levels.get(course.level) ?? []), course]);
    }
    return {
      levels: [...levels.entries()].sort(([a], [b]) => a - b),
      electives: courses.filter((item) => item.type === "elective"),
    };
  }, [plan.data]);

  if (departments.error !== undefined) return <Notice tone="error">{describeError(departments.error)}</Notice>;

  return (
    <div className="space-y-10">
      <Notice tone="info">{t("sample")}</Notice>

      <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <Field id="plan-department" label={t("department")}>
          <Select
            id="plan-department"
            value={department ?? ""}
            onChange={(event) => setChosen(event.target.value)}
            className="sm:w-72"
          >
            {departments.data?.map((item) => (
              <option key={item.code} value={item.code}>
                {localize(item.name, locale)}
              </option>
            ))}
          </Select>
        </Field>
        {plan.data && <p className="text-sm text-muted tabular">{t("total", { hours: plan.data.total_hours })}</p>}
      </div>

      {plan.error !== undefined && <Notice tone="error">{describeError(plan.error)}</Notice>}

      {groups.levels.map(([level, courses]) => (
        <CourseTable key={level} courses={courses} caption={t("level", { level })} />
      ))}

      {plan.data && groups.electives.length > 0 && (
        <div className="space-y-2">
          <CourseTable courses={groups.electives} caption={t("electives")} />
          <p className="text-sm text-muted">{t("electivesHint", { hours: plan.data.elective_hours_required })}</p>
        </div>
      )}
    </div>
  );
}
