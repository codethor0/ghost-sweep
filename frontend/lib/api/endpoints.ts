import { API_PREFIX } from "@/lib/api/config";
import { apiRequest } from "@/lib/api/client";
import type {
  CompanyListResponse,
  CompanyResponse,
  CreateReportPayload,
  HealthStatus,
  JobPostingResponse,
  LoginPayload,
  RegisterPayload,
  ReportResponse,
  ScoreBreakdown,
  TokenResponse,
  UserResponse,
} from "@/lib/api/types";

export function fetchHealthStatus(): Promise<HealthStatus> {
  return apiRequest<HealthStatus>("/health");
}

export function registerUser(payload: RegisterPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(`${API_PREFIX}/auth/register`, {
    method: "POST",
    body: payload,
  });
}

export function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(`${API_PREFIX}/auth/login`, {
    method: "POST",
    body: payload,
  });
}

export function fetchCurrentUser(token: string): Promise<UserResponse> {
  return apiRequest<UserResponse>(`${API_PREFIX}/auth/me`, { token });
}

export function listCompanies(page = 1, pageSize = 20): Promise<CompanyListResponse> {
  return apiRequest<CompanyListResponse>(
    `${API_PREFIX}/companies?page=${page}&page_size=${pageSize}`,
  );
}

export function fetchCompany(companyId: string): Promise<CompanyResponse> {
  return apiRequest<CompanyResponse>(`${API_PREFIX}/companies/${companyId}`);
}

export function fetchCompanyIntegrityScore(companyId: string): Promise<ScoreBreakdown> {
  return apiRequest<ScoreBreakdown>(`${API_PREFIX}/companies/${companyId}/integrity-score`);
}

export function fetchJobPosting(jobPostingId: string): Promise<JobPostingResponse> {
  return apiRequest<JobPostingResponse>(`${API_PREFIX}/job-postings/${jobPostingId}`);
}

export function fetchJobPostingRiskScore(jobPostingId: string): Promise<ScoreBreakdown> {
  return apiRequest<ScoreBreakdown>(`${API_PREFIX}/job-postings/${jobPostingId}/risk-score`);
}

export function createReport(token: string, payload: CreateReportPayload): Promise<ReportResponse> {
  return apiRequest<ReportResponse>(`${API_PREFIX}/reports`, {
    method: "POST",
    token,
    body: payload,
  });
}
