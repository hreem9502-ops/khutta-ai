import { getTranslations, setRequestLocale } from "next-intl/server";
import { Container } from "@/components/layout/Container";
import { PageHeader } from "@/components/layout/PageHeader";

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "About" });
  return { title: t("title"), description: t("lead") };
}

export default async function AboutPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("About");

  return (
    <Container className="max-w-3xl space-y-12">
      <PageHeader title={t("title")} description={t("lead")} />

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">{t("howTitle")}</h2>
        <ol className="space-y-4">
          {(t.raw("how") as string[]).map((paragraph, index) => (
            <li key={paragraph} className="grid grid-cols-[2rem_1fr] gap-2">
              <span className="text-sm font-medium text-brand tabular">{index + 1}</span>
              <p className="text-muted">{paragraph}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">{t("privacyTitle")}</h2>
        <p className="text-muted">{t("privacy")}</p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">{t("limitsTitle")}</h2>
        <p className="text-muted">{t("limits")}</p>
      </section>
    </Container>
  );
}
