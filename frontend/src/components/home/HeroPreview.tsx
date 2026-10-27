import { useLocale, useTranslations } from "next-intl";
import { HERO_PREVIEW_COURSES, HERO_PREVIEW_MAX_HOURS } from "@/lib/hero-preview";
import { localize } from "@/lib/utils";

/** A static sample of the schedule output, so visitors see the result before they start. */
export function HeroPreview() {
  const t = useTranslations("Home");
  const tr = useTranslations("Results");
  const tc = useTranslations("Common");
  const locale = useLocale();
  const total = HERO_PREVIEW_COURSES.reduce((sum, course) => sum + course.hours, 0);

  return (
    <figure className="overflow-hidden rounded-lg border border-line bg-surface" aria-label={t("previewCaption")}>
      <figcaption className="flex items-center justify-between border-b border-line px-5 py-3 text-sm text-muted">
        <span>{t("previewCaption")}</span>
        <span>{t("previewTerm")}</span>
      </figcaption>
      <ul className="divide-y divide-line">
        {HERO_PREVIEW_COURSES.map((course) => (
          <li key={course.code} className="flex items-start justify-between gap-4 px-5 py-4">
            <div className="min-w-0 space-y-0.5">
              <p>
                <span className="text-sm font-medium text-brand" dir="ltr">
                  {course.code}
                </span>
                <span className="ms-3 font-medium">{localize(course.name, locale)}</span>
              </p>
              <p className="text-sm text-muted">{localize(course.note, locale)}</p>
            </div>
            <span className="shrink-0 text-sm text-muted tabular">
              {tc("hours", { hours: course.hours })}
            </span>
          </li>
        ))}
      </ul>
      <div className="flex items-center justify-between border-t border-line bg-subtle px-5 py-3 text-sm">
        <span className="text-muted">{tr("hoursLabel")}</span>
        <span className="font-medium tabular">{tr("hoursValue", { total, max: HERO_PREVIEW_MAX_HOURS })}</span>
      </div>
    </figure>
  );
}
