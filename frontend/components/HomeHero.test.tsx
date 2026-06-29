import { render, screen } from "@testing-library/react";

import { HomeHero } from "@/components/HomeHero";

jest.mock("@/hooks/useHealthStatus", () => ({
  useHealthStatus: () => ({
    health: { status: "ok", service: "ghost-sweep" },
    error: null,
    loading: false,
  }),
}));

describe("HomeHero", () => {
  it("renders the mission statement and platform status", () => {
    render(<HomeHero title="Test title" subtitle="Test subtitle" />);

    expect(screen.getByText("Test title")).toBeInTheDocument();
    expect(screen.getByText("Test subtitle")).toBeInTheDocument();
    expect(screen.getByText("Platform status")).toBeInTheDocument();
    expect(screen.getByText("ok")).toBeInTheDocument();
    expect(screen.getByText("ghost-sweep")).toBeInTheDocument();
  });

  it("renders posting URL notice when provided", () => {
    render(
      <HomeHero
        title="Test title"
        subtitle="Test subtitle"
        postingUrl="https://example.com/jobs/123"
      />,
    );

    expect(screen.getByText("Posting URL from extension")).toBeInTheDocument();
    expect(screen.getByText("https://example.com/jobs/123")).toBeInTheDocument();
    expect(screen.getByText(/Extension handoff is display-only/)).toBeInTheDocument();
  });
});
