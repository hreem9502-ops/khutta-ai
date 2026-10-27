import { useLocale, useTranslations } from "next-intl";
import { Badge } from "@/components/ui";
import { localize } from "@/lib/utils";
import type { Priority, Recommendation } from "@/types";

const PRIORITY_TONE = { high: "brand", medium: "neutral", low: "outline" } as const satisfies Record<
  Priority,
  "brand" | "neutral" | "outline"
>;

/** The recommended courses, one block per course with its reasoning. */
export function ScheduleList({ recommendation }: { recommendation: Recommendation }) {
  const t = useTranslations("Results");
  const tc = useTranslations("Common");
  const locale = useLocale();

  return (
    <div>
      <ul className="divide-y divide-line border-y border-line">
        {recommendation.courses.map((course) => (
          <li key={course.code} className="grid gap-x-6 gap-y-2 py-5 sm:grid-cols-[1fr_auto]">
            <div className="min-w-0 space-y-2">
              <p className="flex flex-wrap items-baseline gap-x-3">
                <span className="text-sm font-medium text-brand" dir="auto">
                  {course.code}
                </span>
                <span className="text-lg font-semibold">{localize(course.name, locale)}</span>
              </p>
              <p className="text-muted">{localize(course.reason, locale)}</p>
              <p className="flex flex-wrap items-center gap-2 pt-1">
                <Badge tone={PRIORITY_TONE[course.priority]}>
                  {t("priority")}: {t(`priorities.${course.priority}`)}
                </Badge>
                <Badge tone="neutral">{t(`types.${course.type}`)}</Badge>
                <Badge tone="neutral">{t("levelBadge", { level: course.level })}</Badge>
              </p>
            </div>
            <p className="font-medium tabular sm:text-end">{tc("hours", { hours: course.credit_hours })}</p>
          </li>
        ))}
      </ul>
      <p className="flex justify-between py-4 text-sm">
        <span className="text-muted">{t("hoursLabel")}</span>
        <span className="font-medium tabular">
          {t("hoursValue", { total: recommendation.total_hours, max: recommendation.max_hours })}
        </span>
      </p>
    </div>
  );
}
