import { render, screen } from "@testing-library/react";

jest.mock("@/components/HomeHero", () => ({
  HomeHero: ({ postingUrl }: { postingUrl?: string }) => (
    <div data-testid="home-hero">{postingUrl ?? ""}</div>
  ),
}));

import HomePage from "./page";

describe("HomePage", () => {
  it("passes posting_url query param to HomeHero", async () => {
    const page = await HomePage({
      searchParams: Promise.resolve({ posting_url: "https://example.com/jobs/123" }),
    });
    render(page);

    expect(screen.getByTestId("home-hero")).toHaveTextContent("https://example.com/jobs/123");
  });

  it("ignores empty posting_url values", async () => {
    const page = await HomePage({
      searchParams: Promise.resolve({ posting_url: "   " }),
    });
    render(page);

    expect(screen.getByTestId("home-hero")).toHaveTextContent("");
  });

  it("uses the first posting_url when an array is provided", async () => {
    const page = await HomePage({
      searchParams: Promise.resolve({
        posting_url: ["https://example.com/a", "https://example.com/b"],
      }),
    });
    render(page);

    expect(screen.getByTestId("home-hero")).toHaveTextContent("https://example.com/a");
  });
});
