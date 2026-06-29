import { render, screen } from "@testing-library/react";

import HomePage from "./page";

jest.mock("@/components/HomeHero", () => ({
  HomeHero: ({ postingUrl }: { postingUrl?: string }) => (
    <div data-testid="home-hero">{postingUrl ?? ""}</div>
  ),
}));

describe("HomePage", () => {
  it("passes posting_url query param to HomeHero", () => {
    render(<HomePage searchParams={{ posting_url: "https://example.com/jobs/123" }} />);

    expect(screen.getByTestId("home-hero")).toHaveTextContent("https://example.com/jobs/123");
  });

  it("ignores empty posting_url values", () => {
    render(<HomePage searchParams={{ posting_url: "   " }} />);

    expect(screen.getByTestId("home-hero")).toHaveTextContent("");
  });

  it("uses the first posting_url when an array is provided", () => {
    render(
      <HomePage searchParams={{ posting_url: ["https://example.com/a", "https://example.com/b"] }} />,
    );

    expect(screen.getByTestId("home-hero")).toHaveTextContent("https://example.com/a");
  });
});
