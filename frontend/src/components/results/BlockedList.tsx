import { ChevronDown } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { localize } from "@/lib/utils";
import type { BlockedCourse } from "@/types";

/** Courses the student cannot take yet, with the prerequisites they are missing. */
export function BlockedList({ courses }: { courses: BlockedCourse[] }) {
  const t = useTranslations("Results");
  const locale = useLocale();

  if (courses.length === 0) return null;

  return (
    <details className="group border-y border-line">
      <summary className="flex cursor-pointer list-none items-center justify-between py-4 font-medium">
        <span>
          {t("blockedTitle")} <span className="text-muted tabular">({courses.length})</span>
        </span>
        <ChevronDown className="h-4 w-4 text-muted transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <p className="pb-3 text-sm text-muted">{t("blockedDescription")}</p>
      <ul className="divide-y divide-line pb-2">
        {courses.map((course) => (
          <li key={course.code} className="flex flex-col gap-1 py-3 sm:flex-row sm:justify-between sm:gap-6">
            <p>
              <span className="text-sm font-medium text-brand" dir="auto">
                {course.code}
              </span>
              <span className="ms-3">{localize(course.name, locale)}</span>
            </p>
            <p className="text-sm text-muted" dir="auto">
              {t("needs", { codes: course.missing_prerequisites.join(", ") })}
            </p>
          </li>
        ))}
      </ul>
    </details>
  );
}
