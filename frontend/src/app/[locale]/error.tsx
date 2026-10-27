"use client";

import { useTranslations } from "next-intl";
import { Container } from "@/components/layout/Container";
import { Button } from "@/components/ui";

/** Route-level error boundary: shows a calm message and lets the user retry. */
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  const t = useTranslations();

  return (
    <Container className="max-w-2xl space-y-4">
      <p className="text-muted">{t("Errors.generic")}</p>
      <Button variant="secondary" onClick={reset}>
        {t("Common.retry")}
      </Button>
    </Container>
  );
}
