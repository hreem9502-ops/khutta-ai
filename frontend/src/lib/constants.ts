import type { Term } from "@/types";

/** Primary navigation. `key` indexes the `Nav` message namespace. */
export const NAV_ITEMS = [
  { key: "home", href: "/", matches: ["/"] },
  { key: "start", href: "/upload", matches: ["/upload", "/review", "/results"] },
  { key: "plan", href: "/plan", matches: ["/plan"] },
  { key: "about", href: "/about", matches: ["/about"] },
] as const;

export const TERMS: readonly Term[] = ["fall", "spring"];

/** Largest upload the backend accepts (keep in sync with MAX_UPLOAD_BYTES; Vercel caps bodies at 4.5 MB). */
export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

/** Key under which the planner state is kept for the browser session. */
export const PLANNER_STORAGE_KEY = "khutta.planner.v1";
