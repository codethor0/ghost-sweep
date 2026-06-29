"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchCurrentUser } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { UserResponse } from "@/lib/api/types";
import { useSession } from "@/lib/session/session-context";
import { DeferredNotice } from "@/components/DeferredNotice";

export function DashboardPanel() {
  const { accessToken, isAuthenticated } = useSession();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchCurrentUser(accessToken)
      .then((profile) => {
        if (!cancelled) {
          setUser(profile);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Unable to load profile.");
          }
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  if (!isAuthenticated) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-bold text-ink">Dashboard</h1>
        <p className="mt-4 text-slate">
          Sign in to view your account. Sessions are in-memory only and do not survive a page
          refresh.
        </p>
        <div className="mt-6 flex gap-4">
          <Link href="/login" className="rounded-md bg-signal px-4 py-2 text-sm font-medium text-white">
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-md border border-slate/20 px-4 py-2 text-sm font-medium text-ink"
          >
            Register
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold text-ink">Dashboard</h1>
      <p className="mt-2 text-sm text-slate">
        Signed in with an in-memory access token. Refreshing this page clears your session.
      </p>

      {loading ? <p className="mt-6 text-sm text-slate">Loading profile...</p> : null}
      {error ? <p className="mt-6 text-sm text-alert">{error}</p> : null}

      {user ? (
        <dl className="mt-8 grid gap-4 rounded-xl border border-slate/10 bg-white p-6 text-sm md:grid-cols-2">
          <div>
            <dt className="font-medium text-ink">Username</dt>
            <dd className="text-slate">{user.username}</dd>
          </div>
          <div>
            <dt className="font-medium text-ink">Email</dt>
            <dd className="text-slate">{user.email}</dd>
          </div>
          <div>
            <dt className="font-medium text-ink">Reputation</dt>
            <dd className="text-slate">{user.reputation_score}</dd>
          </div>
          <div>
            <dt className="font-medium text-ink">Report weight</dt>
            <dd className="text-slate">{user.report_weight}</dd>
          </div>
          <div>
            <dt className="font-medium text-ink">Employer account</dt>
            <dd className="text-slate">{user.is_employer ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt className="font-medium text-ink">Admin</dt>
            <dd className="text-slate">{user.is_admin ? "Yes" : "No"}</dd>
          </div>
        </dl>
      ) : null}

      <div className="mt-8 space-y-4">
        <DeferredNotice title="Deferred in this release">
          Employer claim workflows, moderation tools, evidence upload, and admin panels are not wired
          in the frontend yet. Browse companies and submit reports from posting detail pages.
        </DeferredNotice>
        <Link href="/companies" className="inline-block text-sm font-medium text-signal hover:underline">
          Browse companies
        </Link>
      </div>
    </section>
  );
}
