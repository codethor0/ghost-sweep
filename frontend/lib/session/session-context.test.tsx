import { act, render, screen } from "@testing-library/react";
import { SessionProvider, useSession } from "@/lib/session/session-context";

function TokenReader() {
  const { accessToken, setAccessToken } = useSession();
  return (
    <div>
      <span data-testid="token">{accessToken ?? "none"}</span>
      <button type="button" onClick={() => setAccessToken("in-memory-token")}>
        Set token
      </button>
    </div>
  );
}

describe("SessionProvider", () => {
  it("stores access tokens in React state only", () => {
    render(
      <SessionProvider>
        <TokenReader />
      </SessionProvider>,
    );

    expect(screen.getByTestId("token")).toHaveTextContent("none");
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
      screen.getByRole("button", { name: "Set token" }).click();
    });
    expect(screen.getByTestId("token")).toHaveTextContent("in-memory-token");
    expect(window.localStorage.getItem("accessToken")).toBeNull();
    expect(window.sessionStorage.getItem("accessToken")).toBeNull();
  });
});
