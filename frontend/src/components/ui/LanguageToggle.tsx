"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/routing";

/** Switches between Arabic (RTL) and English (LTR) while staying on the same page. */
export function LanguageToggle() {
  const t = useTranslations("Nav");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const isArabic = locale === "ar";

  return (
    <button
      type="button"
      onClick={() => router.replace(pathname, { locale: isArabic ? "en" : "ar" })}
      className="h-9 rounded-md px-2.5 text-sm font-medium text-muted transition-colors hover:bg-subtle hover:text-ink"
      aria-label={t("switchLanguage")}
      lang={isArabic ? "en" : "ar"}
    >
      {isArabic ? "English" : "العربية"}
    </button>
  );
}
