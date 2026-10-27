import type { ReactNode } from "react";

interface StatBlockProps {
  label: string;
  value: string;
  detail?: string;
  /** Optional visual under the value, such as a progress bar. */
  children?: ReactNode;
}

/** A single headline figure with a label and supporting line. */
export function StatBlock({ label, value, detail, children }: StatBlockProps) {
  return (
    <div className="space-y-2 border-t border-line py-5 first:border-t-0 sm:border-t-0 sm:border-s sm:px-6 sm:first:border-s-0 sm:first:ps-0 sm:last:pe-0">
      <p className="text-sm text-muted">{label}</p>
      <p className="text-2xl font-semibold tracking-tight tabular">{value}</p>
      {children}
      {detail && <p className="text-sm text-muted tabular">{detail}</p>}
    </div>
  );
}
