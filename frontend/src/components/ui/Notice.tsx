import { AlertCircle, CheckCircle2, Info, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Tone = "error" | "warning" | "info" | "success";

const TONES = {
  error: { icon: AlertCircle, styles: "border-danger/30 bg-danger-soft text-danger", role: "alert" },
  warning: { icon: TriangleAlert, styles: "border-warn/30 bg-warn-soft text-warn", role: "status" },
  info: { icon: Info, styles: "border-line bg-subtle text-muted", role: "status" },
  success: { icon: CheckCircle2, styles: "border-ok/30 bg-ok-soft text-ok", role: "status" },
} as const;

interface NoticeProps {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}

/** An inline message block for errors, warnings and notes. */
export function Notice({ tone = "info", children, className }: NoticeProps) {
  const { icon: Icon, styles, role } = TONES[tone];
  return (
    <div role={role} className={cn("flex gap-3 rounded-md border px-4 py-3 text-sm", styles, className)}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
