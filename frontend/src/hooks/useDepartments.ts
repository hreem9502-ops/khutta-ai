import { getDepartments } from "@/lib/api";
import { useApiResource } from "./useApiResource";

/** The departments that have a study plan, loaded once per page. */
export function useDepartments() {
  return useApiResource(getDepartments, "departments");
}
