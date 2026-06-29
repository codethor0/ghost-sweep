"use client";

import { SessionProvider } from "@/lib/session/session-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
