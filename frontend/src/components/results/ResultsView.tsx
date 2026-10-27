"use client";

import { Printer } from "lucide-react";
import { useTranslations } from "next-intl";
import { EmptyState } from "@/components/layout/EmptyState";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button, ButtonLink, Notice } from "@/components/ui";
import { usePlanner } from "@/hooks/usePlanner";
import { useRouter } from "@/i18n/routing";
import { BlockedList } from "./BlockedList";
import { ScheduleList } from "./ScheduleList";
import { StatBlock } from "./StatBlock";
import { SummaryPanel } from "./SummaryPanel";

/** Final step: the validated schedule, its totals, and the courses still out of reach. */
export function ResultsView() {
  const t = useTranslations("Results");
  const tTerms = useTranslations("Terms");
  const router = useRouter();
  const { state, hydrated, reset } = usePlanner();

  if (!hydrated) return null;
  const { recommendation, term } = state;
  if (!recommendation || !term) return <EmptyState />;

  const { progress } = recommendation;
  const percent = Math.round((progress.completed_hours / progress.total_hours) * 100);

  const startOver = () => {
    reset();
    router.push("/upload");
  };

  return (
    <div className="space-y-10">
      <PageHeader
        title={t("title")}
        description={t("description", { term: tTerms(term) })}
        actions={
          <>
            <ButtonLink href="/review" variant="secondary">
              {t("edit")}
            </ButtonLink>
            <Button variant="secondary" onClick={() => window.print()}>
              <Printer className="h-4 w-4" aria-hidden />
              {t("print")}
            </Button>
          </>
        }
      />

      <div className="grid border-b border-line sm:grid-cols-3">
        <StatBlock
          label={t("hoursLabel")}
          value={t("hoursValue", { total: recommendation.total_hours, max: recommendation.max_hours })}
          detail={t("hoursRange", { min: recommendation.min_hours, max: recommendation.max_hours })}
        />
        <StatBlock
          label={t("progressLabel")}
          value={`${percent}%`}
          detail={t("progressDetail", { completed: progress.completed_hours, total: progress.total_hours })}
        >
          <div className="h-1.5 w-full max-w-48 rounded-full bg-subtle" role="presentation">
            <div className="h-full rounded-full bg-brand" style={{ width: `${percent}%` }} />
          </div>
        </StatBlock>
        <StatBlock label={t("remainingLabel")} value={String(progress.remaining_required_courses)} />
      </div>

      {recommendation.courses.length === 0 && <Notice tone="warning">{t("empty")}</Notice>}

      <div className="grid gap-12 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-8">
          {recommendation.courses.length > 0 && <ScheduleList recommendation={recommendation} />}
          <BlockedList courses={recommendation.blocked} />
        </div>
        <SummaryPanel recommendation={recommendation} />
      </div>

      <div className="no-print">
        <Button variant="ghost" onClick={startOver}>
          {t("startOver")}
        </Button>
      </div>
    </div>
  );
}
