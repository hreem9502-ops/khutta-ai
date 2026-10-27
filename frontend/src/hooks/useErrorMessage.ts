import { useTranslations } from "next-intl";
import { ApiError } from "@/lib/api";

/** Returns a function that turns any thrown value into a localised, user-facing message. */
export function useErrorMessage() {
  const t = useTranslations("Errors");

  return (error: unknown): string => {
    if (error instanceof ApiError && t.has(error.code)) return t(error.code);
    return t("generic");
  };
}
