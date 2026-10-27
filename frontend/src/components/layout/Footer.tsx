import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { Container } from "./Container";

/** Minimal site footer with the privacy note and secondary links. */
export function Footer() {
  const t = useTranslations("Footer");
  const tc = useTranslations("Common");
  const tn = useTranslations("Nav");

  return (
    <footer className="no-print mt-24 border-t border-line">
      <Container className="flex flex-col gap-4 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-medium text-ink">{tc("appName")}</span>
          <span className="mx-2 text-line-strong" aria-hidden>
            /
          </span>
          {t("privacy")}
        </p>
        <nav className="flex gap-6" aria-label={t("label")}>
          <Link href="/plan" className="hover:text-ink">
            {tn("plan")}
          </Link>
          <Link href="/about" className="hover:text-ink">
            {tn("about")}
          </Link>
          <Link href="/admin" className="hover:text-ink">
            {t("admin")}
          </Link>
        </nav>
      </Container>
    </footer>
  );
}
