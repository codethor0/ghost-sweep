"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { createReport } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { ReportResponse, ReportType } from "@/lib/api/types";
import { useSession } from "@/lib/session/session-context";
import { DeferredNotice } from "@/components/DeferredNotice";

const REPORT_TYPES: { value: ReportType; label: string }[] = [
  { value: "ghost_job", label: "Ghost job" },
  { value: "no_response", label: "No response" },
  { value: "scam", label: "Scam" },
  { value: "data_harvest", label: "Data harvest" },
  { value: "repost_loop", label: "Repost loop" },
  { value: "stale_posting", label: "Stale posting" },
  { value: "fake_interview", label: "Fake interview" },
];

interface ReportFormProps {
  jobPostingId: string;
}

export function ReportForm({ jobPostingId }: ReportFormProps) {
  const router = useRouter();
  const { accessToken, isAuthenticated } = useSession();
  const [reportType, setReportType] = useState<ReportType>("stale_posting");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<ReportResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const report = await createReport(accessToken, {
        job_posting_id: jobPostingId,
        report_type: reportType,
        description,
      });
      setSuccess(report);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Report submission failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-bold text-ink">Submit report</h1>
        <p className="mt-4 text-slate">
          Sign in to submit a report. Your access token is kept in memory only for this browser tab.
        </p>
        <div className="mt-6 flex gap-4">
          <Link href="/login" className="rounded-md bg-signal px-4 py-2 text-sm font-medium text-white">
            Log in
          </Link>
          <Link href={`/postings/${jobPostingId}`} className="text-sm font-medium text-signal hover:underline">
            Back to posting
          </Link>
        </div>
      </section>
    );
  }

  if (success) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-bold text-ink">Report submitted</h1>
        <p className="mt-4 text-slate">
          Report {success.id} was created with status {success.status}.
        </p>
        <Link
          href={`/postings/${jobPostingId}`}
          className="mt-6 inline-block text-sm font-medium text-signal hover:underline"
        >
          Back to posting
        </Link>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-3xl px-6 py-16">
      <Link
        href={`/postings/${jobPostingId}`}
        className="text-sm font-medium text-signal hover:underline"
      >
        Back to posting
      </Link>
      <h1 className="mt-4 text-3xl font-bold text-ink">Submit report</h1>
      <p className="mt-2 text-sm text-slate">
        Reports require a signed-in session. Evidence upload is deferred.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        <div>
          <label htmlFor="report-type" className="block text-sm font-medium text-ink">
            Report type
          </label>
          <select
            id="report-type"
            value={reportType}
            onChange={(event) => setReportType(event.target.value as ReportType)}
            className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
          >
            {REPORT_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="report-description" className="block text-sm font-medium text-ink">
            Description
          </label>
          <textarea
            id="report-description"
            required
            minLength={20}
            maxLength={5000}
            rows={6}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="mt-1 w-full rounded-md border border-slate/20 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-slate">Minimum 20 characters.</p>
        </div>
        {error ? <p className="text-sm text-alert">{error}</p> : null}
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-signal px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Submitting..." : "Submit report"}
        </button>
      </form>

      <div className="mt-8">
        <DeferredNotice title="Evidence upload deferred">
          File uploads and SHA-256 evidence storage are not wired in the frontend. Attachments
          cannot be added through this form yet.
        </DeferredNotice>
      </div>
    </section>
  );
}
