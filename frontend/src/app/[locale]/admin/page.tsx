import { getTranslations, setRequestLocale } from "next-intl/server";
import { PlanImport } from "@/components/admin/PlanImport";
import { Container } from "@/components/layout/Container";
import { PageHeader } from "@/components/layout/PageHeader";

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Admin" });
  return { title: t("title"), robots: { index: false } };
}

export default async function AdminPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Admin");

  return (
    <Container className="max-w-3xl space-y-10">
      <PageHeader title={t("title")} description={t("description")} />
      <PlanImport />
    </Container>
  );
}
