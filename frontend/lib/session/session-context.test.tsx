import { act, render, screen } from "@testing-library/react";
import { SessionProvider, useSession } from "@/lib/session/session-context";

jest.mock("@/lib/api/endpoints", () => ({
  logoutUser: jest.fn().mockResolvedValue(undefined),
}));

function TokenReader() {
  const { accessToken, refreshToken, setSessionTokens } = useSession();
  return (
    <div>
      <span data-testid="access-token">{accessToken ?? "none"}</span>
      <span data-testid="refresh-token">{refreshToken ?? "none"}</span>
      <button
        type="button"
        onClick={() => setSessionTokens("in-memory-access", "in-memory-refresh")}
      >
        Set tokens
      </button>
    </div>
  );
}

describe("SessionProvider", () => {
  it("stores access and refresh tokens in React state only", () => {
    render(
      <SessionProvider>
        <TokenReader />
      </SessionProvider>,
    );

    expect(screen.getByTestId("access-token")).toHaveTextContent("none");
    expect(screen.getByTestId("refresh-token")).toHaveTextContent("none");
    expect(window.localStorage.getItem("accessToken")).toBeNull();
    expect(window.sessionStorage.getItem("accessToken")).toBeNull();
  });

  it("does not persist tokens to localStorage or sessionStorage", () => {
    render(
      <SessionProvider>
        <TokenReader />
      </SessionProvider>,
    );

    act(() => {
      screen.getByRole("button", { name: "Set tokens" }).click();
    });
    expect(screen.getByTestId("access-token")).toHaveTextContent("in-memory-access");
    expect(screen.getByTestId("refresh-token")).toHaveTextContent("in-memory-refresh");
    expect(window.localStorage.getItem("accessToken")).toBeNull();
    expect(window.sessionStorage.getItem("accessToken")).toBeNull();
  });
});
