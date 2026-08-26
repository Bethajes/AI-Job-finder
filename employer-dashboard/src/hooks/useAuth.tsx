"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import api, {
  clearTokens,
  getAccessToken,
  storeTokens,
} from "@/lib/api";
import type { AuthTokens, User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

export interface RegisterPayload {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  password: string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function fetchMe(): Promise<User> {
  const res = await api.get<User>("/auth/me");
  return res.data;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!getAccessToken()) {
        setIsLoading(false);
        return;
      }
      try {
        const me = await fetchMe();
        if (!cancelled) setUser(me);
      } catch {
        clearTokens();
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post<AuthTokens>("/auth/login", { email, password });
      storeTokens(res.data);
      const me = await fetchMe();
      if (me.role !== "employer" && me.role !== "admin") {
        clearTokens();
        throw new Error(
          "This dashboard is for employer and admin accounts only"
        );
      }
      setUser(me);
      router.push(me.role === "admin" ? "/admin" : "/dashboard");
    },
    [router]
  );

  const register = useCallback(
    async (data: RegisterPayload) => {
      const res = await api.post<AuthTokens>("/auth/register", {
        ...data,
        phone: data.phone || undefined,
        role: "employer",
      });
      storeTokens(res.data);
      const me = await fetchMe();
      if (me.role !== "employer") {
        clearTokens();
        throw new Error("This dashboard is for employer accounts only");
      }
      setUser(me);
      router.push("/dashboard");
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // token may already be invalid; proceed with local cleanup
    }
    clearTokens();
    setUser(null);
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, isLoading, isAuthenticated: !!user, login, register, logout }),
    [user, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
