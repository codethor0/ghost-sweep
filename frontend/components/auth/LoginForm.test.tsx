import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LoginForm } from "@/components/auth/LoginForm";
import { SessionProvider } from "@/lib/session/session-context";
import { ApiError } from "@/lib/api/client";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

jest.mock("@/lib/api/endpoints", () => ({
  loginUser: jest.fn(),
}));

import { loginUser } from "@/lib/api/endpoints";

const mockedLogin = loginUser as jest.MockedFunction<typeof loginUser>;

function renderLoginForm() {
  return render(
    <SessionProvider>
      <LoginForm />
    </SessionProvider>,
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    push.mockReset();
    mockedLogin.mockReset();
  });

  it("submits login and redirects to dashboard", async () => {
    mockedLogin.mockResolvedValue({
      access_token: "access-123",
      refresh_token: "refresh-123",
      token_type: "bearer",
    });

    renderLoginForm();

    fireEvent.change(screen.getByLabelText("Email or username"), { target: { value: "testuser" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalledWith({
        identifier: "testuser",
        password: "password123456",
      });
    });
    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows invalid credentials error", async () => {
    mockedLogin.mockRejectedValue(new ApiError("Invalid credentials", 401));

    renderLoginForm();

    fireEvent.change(screen.getByLabelText("Email or username"), { target: { value: "testuser" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
  });
});
