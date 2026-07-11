import { useEffect } from "react";
import { useSession } from "@/lib/session/session-context";

export function WithAccessToken({
  token,
  children,
}: {
  token: string;
  children: React.ReactNode;
}) {
  const { setSessionTokens } = useSession();

  useEffect(() => {
    setSessionTokens(token, "test-refresh-token");
  }, [setSessionTokens, token]);

  return <>{children}</>;
}
