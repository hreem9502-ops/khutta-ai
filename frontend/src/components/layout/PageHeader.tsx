import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  /** Content shown above the title, such as a step indicator. */
  eyebrow?: ReactNode;
  /** Actions aligned to the end of the header. */
  actions?: ReactNode;
}

/** Title block used at the top of every inner page. */
export function PageHeader({ title, description, eyebrow, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-6 border-b border-line pb-8 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-4">
        {eyebrow}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">{title}</h1>
          {description && <p className="max-w-2xl text-muted">{description}</p>}
        </div>
      </div>
      {actions && <div className="no-print flex shrink-0 items-center gap-3">{actions}</div>}
    </header>
  );
}
