import { getTranslations, setRequestLocale } from "next-intl/server";
import { Container } from "@/components/layout/Container";
import { PageHeader } from "@/components/layout/PageHeader";
import { PlanViewer } from "@/components/plan/PlanViewer";

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Plan" });
  return { title: t("title"), description: t("description") };
}

export default async function PlanPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Plan");

  return (
    <Container className="max-w-3xl space-y-10">
      <PageHeader title={t("title")} description={t("description")} />
      <PlanViewer />
    </Container>
  );
}
