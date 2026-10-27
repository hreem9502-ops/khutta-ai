import { getTranslations, setRequestLocale } from "next-intl/server";
import { Container } from "@/components/layout/Container";
import { FlowStepper } from "@/components/layout/FlowStepper";
import { PageHeader } from "@/components/layout/PageHeader";
import { UploadForm } from "@/components/upload";

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Upload" });
  return { title: t("title"), description: t("description") };
}

export default async function UploadPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("Upload");

  return (
    <Container className="max-w-2xl space-y-10">
      <PageHeader eyebrow={<FlowStepper current={0} />} title={t("title")} description={t("description")} />
      <UploadForm />
    </Container>
  );
}
