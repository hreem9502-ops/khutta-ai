import { useLocale, useTranslations } from "next-intl";
import { Badge, SegmentedControl } from "@/components/ui";
import { localize } from "@/lib/utils";
import type { Course, CourseEntry, CourseState } from "@/types";

interface CourseRowProps {
  course: Course;
  entry: CourseEntry | undefined;
  fromTranscript: boolean;
  onChange: (state: CourseState) => void;
}

const STATES: readonly CourseState[] = ["passed", "in_progress", "none"];

/** One plan course with a control for the student to confirm its status. */
export function CourseRow({ course, entry, fromTranscript, onChange }: CourseRowProps) {
  const t = useTranslations("Review");
  const tc = useTranslations("Common");
  const locale = useLocale();
  const state = entry?.state ?? "none";

  const detail: string[] = [tc("hours", { hours: course.credit_hours })];
  if (entry?.grade) {
    detail.push(state === "none" ? t("failed", { grade: entry.grade }) : t("grade", { grade: entry.grade }));
  }

  return (
    <li className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
      <div className="min-w-0 space-y-1">
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="text-sm font-medium text-brand" dir="auto">
            {course.code}
          </span>
          <span className="font-medium">{localize(course.name, locale)}</span>
          {fromTranscript && <Badge tone="outline">{t("fromTranscript")}</Badge>}
        </p>
        <p className="text-sm text-muted tabular">{detail.join(" · ")}</p>
      </div>
      <SegmentedControl
        name={`status-${course.code}`}
        label={t("statusLabel", { code: course.code })}
        value={state}
        onChange={onChange}
        options={STATES.map((value) => ({ value, label: t(`status.${value}`) }))}
        className="shrink-0 self-start sm:self-auto"
      />
    </li>
  );
}
