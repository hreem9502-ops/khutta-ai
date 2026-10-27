import { cn } from "@/lib/utils";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string> {
  name: string;
  label: string;
  options: readonly Option<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

/**
 * A compact single-choice control built on native radio inputs, so keyboard and
 * screen-reader behaviour comes from the browser.
 */
export function SegmentedControl<T extends string>({
  name,
  label,
  options,
  value,
  onChange,
  className,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={cn("inline-flex rounded-md border border-line-strong bg-surface p-0.5", className)}
    >
      {options.map((option) => (
        <label key={option.value} className="cursor-pointer">
          <input
            type="radio"
            name={name}
            value={option.value}
            checked={option.value === value}
            onChange={() => onChange(option.value)}
            className="peer sr-only"
          />
          <span
            className={cn(
              "block rounded-sm px-2.5 py-1 text-sm text-muted transition-colors",
              "hover:text-ink peer-checked:bg-brand-soft peer-checked:font-medium peer-checked:text-brand",
              "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-brand",
            )}
          >
            {option.label}
          </span>
        </label>
      ))}
    </div>
  );
}
