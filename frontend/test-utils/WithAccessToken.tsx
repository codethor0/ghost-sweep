import { useEffect } from "react";
import { useSession } from "@/lib/session/session-context";

export function WithAccessToken({
  token,
  children,
}: {
  token: string;
  children: React.ReactNode;
}) {
  const { setAccessToken } = useSession();

  useEffect(() => {
    setAccessToken(token);
  }, [setAccessToken, token]);

  return <>{children}</>;
}
