"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { registerUser } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { useSession } from "@/lib/session/session-context";

export function RegisterForm() {
  const router = useRouter();
  const { setAccessToken } = useSession();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const tokens = await registerUser({ email, username, password });
      setAccessToken(tokens.access_token);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="register-email" className="block text-sm font-medium text-ink">
          Email
        </label>
        <input
          id="register-email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="register-username" className="block text-sm font-medium text-ink">
          Username
        </label>
        <input
          id="register-username"
          type="text"
          required
          minLength={3}
          maxLength={64}
          pattern="^[a-zA-Z0-9_\-]+$"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="register-password" className="block text-sm font-medium text-ink">
          Password
        </label>
        <input
          id="register-password"
          type="password"
          required
          minLength={12}
          maxLength={128}
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
        />
        <p className="mt-1 text-xs text-slate">Minimum 12 characters.</p>
      </div>
      {error ? <p className="text-sm text-alert">{error}</p> : null}
      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-signal px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Creating account..." : "Create account"}
      </button>
      <p className="text-sm text-slate">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-signal hover:underline">
          Log in
        </Link>
      </p>
      <p className="text-xs text-slate">
        Your access token is kept in memory for this browser tab only. Refreshing the page clears
        the session.
      </p>
    </form>
  );
}
