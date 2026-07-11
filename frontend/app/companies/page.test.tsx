import { render, screen } from "@testing-library/react";

jest.mock("@/lib/api/endpoints", () => ({
  listCompanies: jest.fn(),
}));

import { listCompanies } from "@/lib/api/endpoints";
import CompaniesPage from "./page";

const mockedListCompanies = listCompanies as jest.MockedFunction<typeof listCompanies>;

describe("CompaniesPage", () => {
  beforeEach(() => {
    mockedListCompanies.mockReset();
  });

  it("shows a clear empty state when no companies exist", async () => {
    mockedListCompanies.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    const page = await CompaniesPage({ searchParams: Promise.resolve({}) });
    render(page);

    expect(screen.getByText("No companies are indexed yet.")).toBeInTheDocument();
    expect(screen.getByText(/Data not available yet/)).toBeInTheDocument();
  });
});
