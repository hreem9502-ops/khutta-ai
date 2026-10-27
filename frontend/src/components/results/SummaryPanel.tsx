import { useLocale, useTranslations } from "next-intl";
import { Notice } from "@/components/ui";
import { localize } from "@/lib/utils";
import type { Recommendation } from "@/types";

/** The advisor's overall summary, any warnings, and how the schedule was produced. */
export function SummaryPanel({ recommendation }: { recommendation: Recommendation }) {
  const t = useTranslations("Results");
  const locale = useLocale();

  return (
    <aside className="space-y-6">
      <div className="space-y-2">
        <h2 className="font-semibold">{t("summaryTitle")}</h2>
        <p className="text-muted">{localize(recommendation.summary, locale)}</p>
        <p className="text-sm text-faint">{t(`source.${recommendation.source}`)}</p>
      </div>

      {recommendation.warnings.length > 0 && (
        <div className="space-y-2">
          <h2 className="font-semibold">{t("warningsTitle")}</h2>
          {recommendation.warnings.map((warning, index) => (
            <Notice key={index} tone="warning">
              {localize(warning, locale)}
            </Notice>
          ))}
        </div>
      )}

      <p className="border-t border-line pt-4 text-sm text-faint">{t("disclaimer")}</p>
    </aside>
  );
}
