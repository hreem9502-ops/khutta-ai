import { useTranslations } from "next-intl";
import { Container } from "@/components/layout/Container";

interface ColumnProps {
  title: string;
  items: string[];
}

function Column({ title, items }: ColumnProps) {
  return (
    <div>
      <h3 className="border-b border-line-strong pb-3 font-semibold">{title}</h3>
      <ul className="divide-y divide-line">
        {items.map((item) => (
          <li key={item} className="py-3 text-muted">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Explains which decisions are made by fixed rules and which are left to the AI. */
export function Responsibilities() {
  const t = useTranslations("Home.split");

  return (
    <section>
      <Container className="space-y-10">
        <div className="max-w-2xl space-y-3">
          <h2 className="text-2xl font-semibold tracking-tight">{t("title")}</h2>
          <p className="text-muted">{t("lead")}</p>
        </div>
        <div className="grid gap-10 md:grid-cols-2">
          <Column title={t("rulesTitle")} items={t.raw("rules") as string[]} />
          <Column title={t("aiTitle")} items={t.raw("ai") as string[]} />
        </div>
        <p className="max-w-2xl border-s-2 border-brand ps-4 text-ink">{t("note")}</p>
      </Container>
    </section>
  );
}
