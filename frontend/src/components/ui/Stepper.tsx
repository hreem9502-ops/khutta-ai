import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepperProps {
  /** Accessible name for the step list. */
  label: string;
  steps: string[];
  /** Zero-based index of the active step. */
  current: number;
}

/** Progress indicator for the three-step planning flow. */
export function Stepper({ label, steps, current }: StepperProps) {
  return (
    <ol className="flex items-center gap-3 text-sm" aria-label={label}>
      {steps.map((label, index) => {
        const done = index < current;
        const active = index === current;
        return (
          <li
            key={label}
            className="flex items-center gap-3"
            aria-current={active ? "step" : undefined}
          >
            <span
              className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-medium tabular",
                active && "bg-brand text-on-brand",
                done && "bg-brand-soft text-brand",
                !active && !done && "border border-line-strong text-faint",
              )}
            >
              {done ? <Check className="h-3.5 w-3.5" aria-hidden /> : index + 1}
            </span>
            <span className={cn(active ? "font-medium text-ink" : "hidden text-muted sm:inline")}>
              {label}
            </span>
            {index < steps.length - 1 && <span className="h-px w-6 bg-line-strong sm:w-10" aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}
