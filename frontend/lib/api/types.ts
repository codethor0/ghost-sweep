export interface HealthStatus {
  status: string;
  service: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  reputation_score: number;
  report_weight: number;
  is_employer: boolean;
  is_admin: boolean;
  employer_company_id: string | null;
  created_at: string;
}

export interface CompanyResponse {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  size: string | null;
  locations: string[];
  integrity_score: number;
  verified_status: string;
  total_postings: number;
  total_hires: number;
  report_count: number;
  created_at: string;
  updated_at: string;
}

export interface CompanyListResponse {
  items: CompanyResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScoreBreakdown {
  score: number;
  breakdown: Record<string, number>;
}

export interface JobPostingResponse {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  url: string;
  source: string;
  posted_date: string | null;
  status: string;
  ghost_risk_score: number;
  repost_count: number;
  original_posting_id: string | null;
  detected_at: string;
  last_seen_at: string;
}

export interface ReportResponse {
  id: string;
  job_posting_id: string;
  reporter_id: string | null;
  report_type: string;
  description: string;
  status: string;
  confidence_score: number;
  verification_votes: number;
  created_at: string;
  updated_at: string;
}

export type ReportType =
  | "ghost_job"
  | "no_response"
  | "scam"
  | "data_harvest"
  | "repost_loop"
  | "stale_posting"
  | "fake_interview";

export interface CreateReportPayload {
  job_posting_id: string;
  report_type: ReportType;
  description: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
}

export interface LoginPayload {
  identifier: string;
  password: string;
}
