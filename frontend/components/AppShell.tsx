"use client";

import Link from "next/link";
import { useSession } from "@/lib/session/session-context";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, clearSession } = useSession();

  return (
    <div className="min-h-screen bg-mist">
      <header className="border-b border-slate/10 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-semibold text-ink">
            ghost-sweep
          </Link>
          <nav className="flex flex-wrap items-center gap-4 text-sm font-medium text-slate">
            <Link href="/companies" className="hover:text-ink">
              Companies
            </Link>
            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="hover:text-ink">
                  Dashboard
                </Link>
                <button
                  type="button"
                  onClick={clearSession}
                  className="hover:text-ink"
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="hover:text-ink">
                  Log in
                </Link>
                <Link href="/register" className="rounded-md bg-signal px-3 py-1.5 text-white hover:bg-signal/90">
                  Register
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
