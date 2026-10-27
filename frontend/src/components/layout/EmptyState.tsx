import { useTranslations } from "next-intl";
import { ButtonLink } from "@/components/ui";

/** Shown when a page is opened without the data it depends on, such as after a fresh visit. */
export function EmptyState() {
  const t = useTranslations("Guard");
  return (
    <div className="flex flex-col items-start gap-4 border-y border-line py-10">
      <p className="text-muted">{t("noData")}</p>
      <ButtonLink href="/upload" variant="secondary">
        {t("start")}
      </ButtonLink>
    </div>
  );
}
