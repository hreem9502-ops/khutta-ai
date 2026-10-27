"use client";

import { ThemeProvider } from "next-themes";
import type { ReactNode } from "react";
import { PlannerProvider } from "./PlannerProvider";

/** Client-side providers shared by every page. */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <PlannerProvider>{children}</PlannerProvider>
    </ThemeProvider>
  );
}
