import Link from "next/link";
import { listCompanies } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { DeferredNotice } from "@/components/DeferredNotice";

interface CompaniesPageProps {
  searchParams?: Promise<{ page?: string }>;
}

export default async function CompaniesPage({ searchParams }: CompaniesPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const page = Number(resolvedSearchParams?.page ?? "1") || 1;
  let error: string | null = null;
  let data = null;

  try {
    data = await listCompanies(page);
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Unable to load companies.";
  }

  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="text-3xl font-bold text-ink">Companies</h1>
      <p className="mt-2 text-slate">Public company profiles from the ghost-sweep API.</p>

      {error ? <p className="mt-6 text-sm text-alert">{error}</p> : null}

      {data && data.items.length === 0 ? (
        <div className="mt-8 space-y-4">
          <p className="text-sm text-slate">No companies are indexed yet.</p>
          <DeferredNotice title="Data not available yet">
            Company records are created through backend ingestion and employer workflows. This page
            will populate as data is added to the database.
          </DeferredNotice>
        </div>
      ) : null}

      {data && data.items.length > 0 ? (
        <>
          <ul className="mt-8 divide-y divide-slate/10 rounded-xl border border-slate/10 bg-white">
            {data.items.map((company) => (
              <li key={company.id} className="p-6">
                <Link href={`/companies/${company.id}`} className="block hover:opacity-90">
                  <h2 className="text-lg font-semibold text-ink">{company.name}</h2>
                  <p className="mt-1 text-sm text-slate">
                    Integrity score {company.integrity_score.toFixed(1)} | {company.total_postings}{" "}
                    postings | {company.report_count} reports
                  </p>
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm text-slate">
            Page {data.page} of {Math.max(1, Math.ceil(data.total / data.page_size))} ({data.total}{" "}
            total)
          </p>
        </>
      ) : null}
    </section>
  );
}
