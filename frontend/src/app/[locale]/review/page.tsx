import { getTranslations, setRequestLocale } from "next-intl/server";
import { Container } from "@/components/layout/Container";
import { FlowStepper } from "@/components/layout/FlowStepper";
import { PageHeader } from "@/components/layout/PageHeader";
import { ReviewForm } from "@/components/review";

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Review" });
  return { title: t("title"), description: t("description") };
}

export default async function ReviewPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Review");

  return (
    <Container className="max-w-3xl space-y-10">
      <PageHeader eyebrow={<FlowStepper current={1} />} title={t("title")} description={t("description")} />
      <ReviewForm />
    </Container>
  );
}
