import { apiRequest, ApiError } from "@/lib/api/client";

describe("apiRequest", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("returns parsed JSON on success", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: "ok", service: "ghost-sweep" }),
    }) as jest.Mock;

    const result = await apiRequest<{ status: string; service: string }>("/health");
    expect(result).toEqual({ status: "ok", service: "ghost-sweep" });
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("sends bearer token and JSON body", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ access_token: "abc" }),
    }) as jest.Mock;

    await apiRequest("/api/v1/auth/login", {
      method: "POST",
      token: "secret",
      body: { identifier: "user", password: "password123456" },
    });

    const [, options] = (global.fetch as jest.Mock).mock.calls[0] as [string, RequestInit];
    expect(options.headers).toBeInstanceOf(Headers);
    expect((options.headers as Headers).get("Authorization")).toBe("Bearer secret");
    expect((options.headers as Headers).get("Content-Type")).toBe("application/json");
    expect(options.body).toBe(JSON.stringify({ identifier: "user", password: "password123456" }));
  });

  it("throws ApiError with backend detail", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({ detail: "Invalid credentials" }),
    }) as jest.Mock;

    await expect(apiRequest("/api/v1/auth/login", { method: "POST" })).rejects.toEqual(
      new ApiError("Invalid credentials", 401),
    );
  });

  it("formats validation errors without raw JSON", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: async () => ({
        detail: [
          {
            type: "value_error",
            loc: ["body", "email"],
            msg: "value is not a valid email address",
            input: "",
          },
          {
            type: "string_too_short",
            loc: ["body", "password"],
            msg: "String should have at least 12 characters",
            input: "short",
          },
        ],
      }),
    }) as jest.Mock;

    await expect(apiRequest("/api/v1/auth/register", { method: "POST" })).rejects.toEqual(
      new ApiError(
        "email: value is not a valid email address; password: String should have at least 12 characters",
        422,
      ),
    );
  });
});
