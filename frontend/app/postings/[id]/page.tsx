import Link from "next/link";
import { notFound } from "next/navigation";
import {
  fetchCompany,
  fetchJobPosting,
  fetchJobPostingRiskScore,
} from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { DeferredNotice } from "@/components/DeferredNotice";

interface PostingDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function PostingDetailPage({ params }: PostingDetailPageProps) {
  const { id } = await params;
  let posting = null;
  let riskScore = null;
  let companyName: string | null = null;

  try {
    posting = await fetchJobPosting(id);
    riskScore = await fetchJobPostingRiskScore(id);
    const company = await fetchCompany(posting.company_id);
    companyName = company.name;
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <Link href="/companies" className="text-sm font-medium text-signal hover:underline">
        Browse companies
      </Link>
      <h1 className="mt-4 text-3xl font-bold text-ink">{posting.title}</h1>
      <p className="mt-2 text-slate">
        {companyName ? (
          <>
            at{" "}
            <Link href={`/companies/${posting.company_id}`} className="font-medium text-signal hover:underline">
              {companyName}
            </Link>
          </>
        ) : (
          "Company profile unavailable"
        )}
      </p>

      <dl className="mt-8 grid gap-4 rounded-xl border border-slate/10 bg-white p-6 text-sm md:grid-cols-2">
        <div>
          <dt className="font-medium text-ink">Status</dt>
          <dd className="text-slate">{posting.status}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">Source</dt>
          <dd className="text-slate">{posting.source}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">Ghost risk score</dt>
          <dd className="text-slate">{posting.ghost_risk_score.toFixed(1)}</dd>
        </div>
        <div>
          <dt className="font-medium text-ink">Repost count</dt>
          <dd className="text-slate">{posting.repost_count}</dd>
        </div>
        <div className="md:col-span-2">
          <dt className="font-medium text-ink">URL</dt>
          <dd className="break-all text-slate">
            <a href={posting.url} className="text-signal hover:underline" target="_blank" rel="noreferrer">
              {posting.url}
            </a>
          </dd>
        </div>
        {posting.description ? (
          <div className="md:col-span-2">
            <dt className="font-medium text-ink">Description</dt>
            <dd className="text-slate">{posting.description}</dd>
          </div>
        ) : null}
      </dl>

      {riskScore ? (
        <div className="mt-8 rounded-xl border border-slate/10 bg-white p-6">
          <h2 className="text-base font-semibold text-ink">Risk score breakdown</h2>
          <p className="mt-2 text-sm text-slate">Current score: {riskScore.score.toFixed(1)}</p>
          <ul className="mt-4 space-y-2 text-sm text-slate">
            {Object.entries(riskScore.breakdown).map(([key, value]) => (
              <li key={key}>
                {key}: {value.toFixed(1)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-8 flex flex-col gap-4">
        <Link
          href={`/postings/${posting.id}/report`}
          className="inline-flex w-fit rounded-md bg-signal px-4 py-2 text-sm font-medium text-white"
        >
          Submit a report
        </Link>
        <DeferredNotice title="Deferred in this release">
          Community votes, evidence file upload, and moderation status updates are not available in
          the frontend yet.
        </DeferredNotice>
      </div>
    </section>
  );
}
