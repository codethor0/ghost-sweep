import { render, screen, waitFor } from "@testing-library/react";
import { DashboardPanel } from "@/components/dashboard/DashboardPanel";
import { SessionProvider } from "@/lib/session/session-context";
import { WithAccessToken } from "@/test-utils/WithAccessToken";

jest.mock("@/lib/api/endpoints", () => ({
  fetchCurrentUser: jest.fn(),
}));

import { fetchCurrentUser } from "@/lib/api/endpoints";

const mockedFetchCurrentUser = fetchCurrentUser as jest.MockedFunction<typeof fetchCurrentUser>;

function AuthenticatedDashboard() {
  return (
    <WithAccessToken token="token-abc">
      <DashboardPanel />
    </WithAccessToken>
  );
}

describe("DashboardPanel", () => {
  beforeEach(() => {
    mockedFetchCurrentUser.mockReset();
  });

  it("prompts unauthenticated users to sign in", () => {
    render(
      <SessionProvider>
        <DashboardPanel />
      </SessionProvider>,
    );

    expect(screen.getByText(/Sign in to view your account/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute("href", "/login");
  });

  it("loads current user profile when authenticated", async () => {
    mockedFetchCurrentUser.mockResolvedValue({
      id: "user-1",
      email: "test@example.com",
      username: "testuser",
      reputation_score: 1,
      report_weight: 1,
      is_employer: false,
      is_admin: false,
      employer_company_id: null,
      created_at: "2026-01-01T00:00:00Z",
    });

    render(
      <SessionProvider>
        <AuthenticatedDashboard />
      </SessionProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });
    expect(mockedFetchCurrentUser).toHaveBeenCalledWith("token-abc");
    expect(screen.getByText(/in-memory access token/)).toBeInTheDocument();
  });
});
