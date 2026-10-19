"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import {
  type AdminMe,
  getMe,
  login as apiLogin,
  logout as apiLogout,
  AdminAuthError,
} from "@/lib/adminAuth";

type AdminAuthContextValue = {
  user: AdminMe | null;
  loading: boolean;
  loginError: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  handleApiError: (err: unknown) => string | null;
};

const AdminAuthContext = createContext<AdminAuthContextValue | null>(null);

export function useAdminAuth(): AdminAuthContextValue {
  const ctx = useContext(AdminAuthContext);
  if (!ctx) {
    throw new Error("useAdminAuth must be inside AdminAuthProvider");
  }
  return ctx;
}

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AdminMe | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loginError, setLoginError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
    } catch (err) {
      if (err instanceof AdminAuthError && err.status === 401) {
        setUser(null);
      } else {
        console.error("[adminAuth] refresh failed", err);
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await refresh();
      if (!cancelled) setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const login = useCallback(
    async (username: string, password: string): Promise<boolean> => {
      setLoginError(null);
      try {
        await apiLogin(username, password);
        const me = await getMe();
        setUser(me);
        return true;
      } catch (err) {
        if (err instanceof AdminAuthError) {
          if (err.status === 401) {
            setLoginError("Identifiants invalides.");
          } else {
            setLoginError(err.message || "Erreur de connexion.");
          }
        } else {
          setLoginError("Erreur réseau. Vérifiez que le serveur est actif.");
        }
        return false;
      }
    },
    []
  );

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
    setLoginError(null);
  }, []);

  const handleApiError = useCallback(
    (err: unknown): string | null => {
      if (err instanceof AdminAuthError) {
        if (err.status === 401) {
          setUser(null);
          router.replace("/admin/login");
          return null;
        }
        return err.message;
      }
      return "Erreur réseau. Veuillez réessayer.";
    },
    [router]
  );

  return (
    <AdminAuthContext.Provider
      value={{
        user,
        loading,
        loginError,
        login,
        logout,
        refresh,
        handleApiError,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
}
