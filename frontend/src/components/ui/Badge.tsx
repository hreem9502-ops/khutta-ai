import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Tone = "brand" | "neutral" | "outline";

const TONES: Record<Tone, string> = {
  brand: "bg-brand-soft text-brand",
  neutral: "bg-subtle text-muted",
  outline: "border border-line-strong text-muted",
};

interface BadgeProps {
  tone?: Tone;
  children: ReactNode;
}

/** A small inline label for categories and priorities. */
export function Badge({ tone = "neutral", children }: BadgeProps) {
  return (
    <span className={cn("inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium", TONES[tone])}>
      {children}
    </span>
  );
}
