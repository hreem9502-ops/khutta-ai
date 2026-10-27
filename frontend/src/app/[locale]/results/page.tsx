import { getTranslations, setRequestLocale } from "next-intl/server";
import { Container } from "@/components/layout/Container";
import { FlowStepper } from "@/components/layout/FlowStepper";
import { ResultsView } from "@/components/results";

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Results" });
  return { title: t("title") };
}

export default async function ResultsPage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <Container className="space-y-8">
      <div className="no-print">
        <FlowStepper current={2} />
      </div>
      <ResultsView />
    </Container>
  );
}
