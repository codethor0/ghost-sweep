import Link from "next/link";
import { notFound } from "next/navigation";
import {
  fetchCompany,
  fetchCompanyIntegrityScore,
} from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { DeferredNotice } from "@/components/DeferredNotice";

interface CompanyDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function CompanyDetailPage({ params }: CompanyDetailPageProps) {
  const { id } = await params;
  let company = null;
  let score = null;

  try {
    company = await fetchCompany(id);
    score = await fetchCompanyIntegrityScore(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <Link href="/companies" className="text-sm font-medium text-signal hover:underline">
        Back to companies
      </Link>
      <h1 className="mt-4 text-3xl font-bold text-ink">{company.name}</h1>
      <p className="mt-2 text-slate">
        {company.domain ?? "No domain on file"} | Verified status: {company.verified_status}
      </p>

      <dl className="mt-8 grid gap-4 rounded-xl border border-slate/10 bg-white p-6 text-sm md:grid-cols-2">
        <div>
          <dt className="font-medium text-ink">Industry</dt>
          <dd className="text-slate">{company.industry ?? "Not listed"}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">Size</dt>
          <dd className="text-slate">{company.size ?? "Not listed"}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">Integrity score</dt>
          <dd className="text-slate">{company.integrity_score.toFixed(1)}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">Postings / hires / reports</dt>
          <dd className="text-slate">
            {company.total_postings} / {company.total_hires} / {company.report_count}
          </dd>
        </div>
        <div className="md:col-span-2">
          <dt className="font-medium text-ink">Locations</dt>
          <dd className="text-slate">
            {company.locations.length > 0 ? company.locations.join(", ") : "None listed"}
          </dd>
        </div>
      </dl>

      {score ? (
        <div className="mt-8 rounded-xl border border-slate/10 bg-white p-6">
          <h2 className="text-base font-semibold text-ink">Integrity score breakdown</h2>
          <p className="mt-2 text-sm text-slate">Current score: {score.score.toFixed(1)}</p>
          <ul className="mt-4 space-y-2 text-sm text-slate">
            {Object.entries(score.breakdown).map(([key, value]) => (
              <li key={key}>
                {key}: {value.toFixed(1)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-8 space-y-4">
        <DeferredNotice title="Posting list not wired">
          Individual job postings for this company are not listed here yet. Open a posting by ID
          from API data or future ingestion views.
        </DeferredNotice>
      </div>
    </section>
  );
}
