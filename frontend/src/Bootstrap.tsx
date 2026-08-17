import { GoogleOAuthProvider } from "@react-oauth/google";
import { useEffect, useState, type ReactNode } from "react";
import { AuthProvider } from "./context/AuthContext";
import { GoogleConfigContext } from "./context/GoogleConfigContext";

async function resolveAuthConfig(): Promise<{ clientId: string; devAuthEnabled: boolean }> {
  const fromVite =
    import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim() ||
    import.meta.env.GOOGLE_CLIENT_ID?.trim();

  try {
    const res = await fetch("/api/v1/auth/config");
    if (res.ok) {
      const data = (await res.json()) as {
        google_client_id?: string;
        dev_auth_enabled?: boolean;
      };
      return {
        clientId: fromVite || data.google_client_id?.trim() || "",
        devAuthEnabled: Boolean(data.dev_auth_enabled),
      };
    }
  } catch {
    /* backend may be down */
  }

  return { clientId: fromVite || "", devAuthEnabled: !fromVite };
}

export default function Bootstrap({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<{ clientId: string; devAuthEnabled: boolean } | null>(null);

  useEffect(() => {
    resolveAuthConfig().then(setConfig);
  }, []);

  if (config === null) {
    return <div className="page-loading full">Loading…</div>;
  }

  const inner = (
    <GoogleConfigContext.Provider value={config}>
      <AuthProvider>{children}</AuthProvider>
    </GoogleConfigContext.Provider>
  );

  if (!config.clientId) {
    return inner;
  }

  return <GoogleOAuthProvider clientId={config.clientId}>{inner}</GoogleOAuthProvider>;
}
