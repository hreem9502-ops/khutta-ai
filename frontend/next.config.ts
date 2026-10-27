import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin();

/**
 * The browser always calls `/api/...` on its own origin. On Vercel the project's top-level
 * rewrite sends those requests to the FastAPI service; in local development this rewrite
 * forwards them to the backend started with uvicorn.
 */
const DEV_API_TARGET = process.env.API_DEV_TARGET ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [{ source: "/api/:path*", destination: `${DEV_API_TARGET}/api/:path*` }];
  },
};

export default withNextIntl(nextConfig);
