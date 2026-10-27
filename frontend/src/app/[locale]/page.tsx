import { setRequestLocale } from "next-intl/server";
import { Hero, HowItWorks, Responsibilities } from "@/components/home";

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <div className="space-y-28">
      <Hero />
      <HowItWorks />
      <Responsibilities />
    </div>
  );
}
