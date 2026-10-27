import { useTranslations } from "next-intl";
import { Container } from "@/components/layout/Container";

const STEP_KEYS = ["upload", "review", "verify", "schedule"] as const;

export function HowItWorks() {
  const t = useTranslations("Home");

  return (
    <section id="how-it-works" className="scroll-mt-20">
      <Container className="space-y-10">
        <h2 className="text-2xl font-semibold tracking-tight">{t("stepsTitle")}</h2>
        <ol className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {STEP_KEYS.map((key, index) => (
            <li key={key} className="space-y-3 border-t border-line-strong pt-4">
              <span className="text-sm font-medium text-brand tabular">{String(index + 1).padStart(2, "0")}</span>
              <h3 className="font-semibold">{t(`steps.${key}.title`)}</h3>
              <p className="text-sm text-muted">{t(`steps.${key}.body`)}</p>
            </li>
          ))}
        </ol>
      </Container>
    </section>
  );
}
