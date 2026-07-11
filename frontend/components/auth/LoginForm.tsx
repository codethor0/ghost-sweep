"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { loginUser } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { useSession } from "@/lib/session/session-context";

export function LoginForm() {
  const router = useRouter();
  const { setSessionTokens } = useSession();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const tokens = await loginUser({ identifier, password });
      setSessionTokens(tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="login-identifier" className="block text-sm font-medium text-ink">
          Email or username
        </label>
        <input
          id="login-identifier"
          type="text"
          required
          minLength={3}
          autoComplete="username"
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="login-password" className="block text-sm font-medium text-ink">
          Password
        </label>
        <input
          id="login-password"
          type="password"
          required
          minLength={12}
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
        />
      </div>
      {error ? <p className="text-sm text-alert">{error}</p> : null}
      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-signal px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Signing in..." : "Sign in"}
      </button>
      <p className="text-sm text-slate">
        Need an account?{" "}
        <Link href="/register" className="font-medium text-signal hover:underline">
          Register
        </Link>
      </p>
      <p className="text-xs text-slate">
        Your access token is kept in memory for this browser tab only. Refreshing the page clears
        the session.
      </p>
    </form>
  );
}
