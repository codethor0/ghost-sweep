import { render, screen, waitFor } from "@testing-library/react";
import { ReportForm } from "@/components/reports/ReportForm";
import { SessionProvider } from "@/lib/session/session-context";
import { WithAccessToken } from "@/test-utils/WithAccessToken";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

describe("ReportForm", () => {
  it("requires sign in before submission", () => {
    render(
      <SessionProvider>
        <ReportForm jobPostingId="posting-1" />
      </SessionProvider>,
    );

    expect(screen.getByText(/Sign in to submit a report/)).toBeInTheDocument();
    expect(screen.queryByText(/Evidence upload deferred/)).not.toBeInTheDocument();
  });

  it("shows deferred evidence notice for authenticated users", async () => {
    render(
      <SessionProvider>
        <WithAccessToken token="token-abc">
          <ReportForm jobPostingId="posting-1" />
        </WithAccessToken>
      </SessionProvider>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Report type")).toBeInTheDocument();
    });
    expect(screen.getByText(/Evidence upload deferred/)).toBeInTheDocument();
  });

  it("documents minimum description length for authenticated users", async () => {
    render(
      <SessionProvider>
        <WithAccessToken token="token-abc">
          <ReportForm jobPostingId="posting-1" />
        </WithAccessToken>
      </SessionProvider>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Description")).toBeInTheDocument();
    });
    expect(screen.getByText(/Minimum 20 characters/)).toBeInTheDocument();
  });
});
