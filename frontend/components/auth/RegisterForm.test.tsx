import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { SessionProvider } from "@/lib/session/session-context";
import { ApiError } from "@/lib/api/client";

const push = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

jest.mock("@/lib/api/endpoints", () => ({
  registerUser: jest.fn(),
}));

import { registerUser } from "@/lib/api/endpoints";

const mockedRegister = registerUser as jest.MockedFunction<typeof registerUser>;

function renderRegisterForm() {
  return render(
    <SessionProvider>
      <RegisterForm />
    </SessionProvider>,
  );
}

describe("RegisterForm", () => {
  beforeEach(() => {
    push.mockReset();
    mockedRegister.mockReset();
  });

  it("submits registration and stores access token in session", async () => {
    mockedRegister.mockResolvedValue({
      access_token: "access-123",
      refresh_token: "refresh-123",
      token_type: "bearer",
    });

    renderRegisterForm();

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "testuser" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(mockedRegister).toHaveBeenCalledWith({
        email: "test@example.com",
        username: "testuser",
        password: "password123456",
      });
    });
    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows API error message", async () => {
    mockedRegister.mockRejectedValue(new ApiError("Email already registered", 409));

    renderRegisterForm();

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "testuser" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText("Email already registered")).toBeInTheDocument();
  });
});
