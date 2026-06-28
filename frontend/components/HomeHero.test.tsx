import { render, screen } from "@testing-library/react";

import { HomeHero } from "@/components/HomeHero";

jest.mock("@/hooks/useHealthStatus", () => ({
  useHealthStatus: () => ({
    health: { status: "healthy", database: "healthy", redis: "healthy" },
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
    expect(screen.getAllByText("healthy")).toHaveLength(3);
  });
});
