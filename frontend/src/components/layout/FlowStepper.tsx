import { useTranslations } from "next-intl";
import { Stepper } from "@/components/ui";

/** Step indicator for the upload, review and results pages. `current` is zero-based. */
export function FlowStepper({ current }: { current: number }) {
  const t = useTranslations("Flow");
  return <Stepper label={t("label")} steps={[t("upload"), t("review"), t("results")]} current={current} />;
}
