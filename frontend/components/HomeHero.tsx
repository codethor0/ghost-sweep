"use client";

import { useHealthStatus } from "@/hooks/useHealthStatus";

export interface HomeHeroProps {
  title: string;
  subtitle: string;
}

export function HomeHero({ title, subtitle }: HomeHeroProps) {
  const { health, error, loading } = useHealthStatus();

  return (
    <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-signal">Job Integrity Database</p>
      <h1 className="mt-4 text-5xl font-bold tracking-tight text-ink">{title}</h1>
      <p className="mt-6 max-w-3xl text-lg leading-8 text-slate">{subtitle}</p>

      <div className="mt-10 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate/10 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Evidence-based reports</h2>
          <p className="mt-2 text-sm leading-6 text-slate">
            Users submit job posting URLs, timelines, categories, and supporting evidence.
          </p>
        </article>
        <article className="rounded-xl border border-slate/10 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Transparent risk signals</h2>
          <p className="mt-2 text-sm leading-6 text-slate">
            Scores show raw inputs, weighted calculations, confidence, and plain-language explanations.
          </p>
        </article>
        <article className="rounded-xl border border-slate/10 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Employer response path</h2>
          <p className="mt-2 text-sm leading-6 text-slate">
            Companies can claim profiles, verify active roles, respond, and dispute incorrect reports.
          </p>
        </article>
      </div>

      <div className="mt-10 rounded-xl border border-slate/10 bg-white p-6">
        <h2 className="text-base font-semibold text-ink">Platform status</h2>
        {loading ? <p className="mt-2 text-sm text-slate">Checking API health...</p> : null}
        {error ? <p className="mt-2 text-sm text-alert">API unavailable: {error}</p> : null}
        {health ? (
          <dl className="mt-4 grid gap-2 text-sm text-slate md:grid-cols-3">
            <div>
              <dt className="font-medium text-ink">Service</dt>
              <dd>{health.status}</dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Database</dt>
              <dd>{health.database}</dd>
            </div>
            <div>
              <dt className="font-medium text-ink">Redis</dt>
              <dd>{health.redis}</dd>
            </div>
          </dl>
        ) : null}
      </div>
    </section>
  );
}
