import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Locale, LocalizedText } from "@/types";

/** Merges Tailwind classes, resolving conflicts in favour of the last one. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Picks the string for `locale` from a bilingual text. */
export function localize(text: LocalizedText, locale: string): string {
  return text[locale as Locale] ?? text.en;
}

/** Formats a byte count for display, for example `1.4 MB`. */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
