import {
  createReport,
  fetchCurrentUser,
  listCompanies,
  loginUser,
  registerUser,
} from "@/lib/api/endpoints";

jest.mock("@/lib/api/client", () => ({
  apiRequest: jest.fn(),
}));

import { apiRequest } from "@/lib/api/client";

const mockedApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

describe("api endpoints", () => {
  beforeEach(() => {
    mockedApiRequest.mockReset();
  });

  it("registerUser posts to auth register", async () => {
    mockedApiRequest.mockResolvedValue({ access_token: "a", refresh_token: "r", token_type: "bearer" });
    await registerUser({ email: "a@b.com", username: "user", password: "password123456" });
    expect(mockedApiRequest).toHaveBeenCalledWith("/api/v1/auth/register", {
      method: "POST",
      body: { email: "a@b.com", username: "user", password: "password123456" },
    });
  });

  it("loginUser posts to auth login", async () => {
    mockedApiRequest.mockResolvedValue({ access_token: "a", refresh_token: "r", token_type: "bearer" });
    await loginUser({ identifier: "user", password: "password123456" });
    expect(mockedApiRequest).toHaveBeenCalledWith("/api/v1/auth/login", {
      method: "POST",
      body: { identifier: "user", password: "password123456" },
    });
  });

  it("fetchCurrentUser sends token", async () => {
    mockedApiRequest.mockResolvedValue({ id: "1", email: "a@b.com", username: "user" });
    await fetchCurrentUser("token-1");
    expect(mockedApiRequest).toHaveBeenCalledWith("/api/v1/auth/me", { token: "token-1" });
  });

  it("listCompanies includes pagination", async () => {
    mockedApiRequest.mockResolvedValue({ items: [], total: 0, page: 2, page_size: 20 });
    await listCompanies(2, 20);
    expect(mockedApiRequest).toHaveBeenCalledWith("/api/v1/companies?page=2&page_size=20");
  });

  it("createReport posts with token", async () => {
    mockedApiRequest.mockResolvedValue({ id: "report-1" });
    await createReport("token-1", {
      job_posting_id: "posting-1",
      report_type: "stale_posting",
      description: "This posting has been open for months without updates.",
    });
    expect(mockedApiRequest).toHaveBeenCalledWith("/api/v1/reports", {
      method: "POST",
      token: "token-1",
      body: {
        job_posting_id: "posting-1",
        report_type: "stale_posting",
        description: "This posting has been open for months without updates.",
      },
    });
  });
});
