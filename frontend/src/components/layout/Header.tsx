"use client";

import { Menu, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { LanguageToggle, ThemeToggle } from "@/components/ui";
import { Link, usePathname } from "@/i18n/routing";
import { NAV_ITEMS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Container } from "./Container";

/** Site header with the wordmark, primary navigation and display toggles. */
export function Header() {
  const t = useTranslations("Nav");
  const tc = useTranslations("Common");
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (matches: readonly string[]) =>
    matches.some((prefix) => (prefix === "/" ? pathname === "/" : pathname.startsWith(prefix)));

  return (
    <header className="no-print sticky top-0 z-30 border-b border-line bg-canvas">
      <Container className="flex h-14 items-center justify-between gap-4">
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-2.5" onClick={() => setMenuOpen(false)}>
            <span className="h-5 w-1 rounded-sm bg-brand" aria-hidden />
            <span className="text-lg font-semibold tracking-tight">{tc("appName")}</span>
          </Link>

          <nav className="hidden items-center gap-6 md:flex" aria-label={t("label")}>
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.key}
                href={item.href}
                aria-current={isActive(item.matches) ? "page" : undefined}
                className={cn(
                  "py-4 text-sm transition-colors",
                  isActive(item.matches)
                    ? "border-b-2 border-brand font-medium text-ink"
                    : "border-b-2 border-transparent text-muted hover:text-ink",
                )}
              >
                {t(item.key)}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-1">
          <LanguageToggle />
          <ThemeToggle />
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-md text-muted hover:bg-subtle hover:text-ink md:hidden"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-label={t("menu")}
          >
            {menuOpen ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
          </button>
        </div>
      </Container>

      {menuOpen && (
        <nav className="border-t border-line bg-canvas md:hidden" aria-label={t("label")}>
          <Container className="flex flex-col py-2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.key}
                href={item.href}
                onClick={() => setMenuOpen(false)}
                aria-current={isActive(item.matches) ? "page" : undefined}
                className={cn(
                  "py-3 text-sm",
                  isActive(item.matches) ? "font-medium text-ink" : "text-muted",
                )}
              >
                {t(item.key)}
              </Link>
            ))}
          </Container>
        </nav>
      )}
    </header>
  );
}
