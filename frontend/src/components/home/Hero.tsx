import { useTranslations } from "next-intl";
import { Container } from "@/components/layout/Container";
import { ButtonLink } from "@/components/ui";
import { HeroPreview } from "./HeroPreview";

export function Hero() {
  const t = useTranslations("Home");

  return (
    <section>
      <Container className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <div className="space-y-6">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-5xl">
            {t("title")}
          </h1>
          <p className="max-w-xl text-lg text-muted">{t("lead")}</p>
          <div className="flex flex-wrap gap-3 pt-2">
            <ButtonLink href="/upload" size="lg">
              {t("start")}
            </ButtonLink>
            <ButtonLink href="/about" variant="secondary" size="lg">
              {t("learnMore")}
            </ButtonLink>
          </div>
        </div>
        <HeroPreview />
      </Container>
    </section>
  );
}
