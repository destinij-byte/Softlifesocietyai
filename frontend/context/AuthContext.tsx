import React, { createContext, useContext, useEffect, useState } from "react";
import { apiRequest, getToken, setToken, setUnauthorizedHandler } from "@/services/api";
import { AuthResponse, User } from "@/services/types";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  logIn: (email: string, password: string) => Promise<void>;
  logOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const bootstrap = async () => {
    const token = await getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await apiRequest<User>("/auth/me");
      setUser(me);
    } catch {
      await setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    bootstrap();
    // A 401 anywhere in the app (expired/revoked token) should drop the user
    // back to the auth flow, not just silently fail the one request.
    setUnauthorizedHandler(() => setUser(null));
    return () => setUnauthorizedHandler(null);
  }, []);

  const handleAuthResponse = async (res: AuthResponse) => {
    await setToken(res.access_token);
    setUser(res.user);
  };

  const signUp = async (name: string, email: string, password: string) => {
    const res = await apiRequest<AuthResponse>("/auth/signup", {
      method: "POST",
      body: { name, email, password },
      auth: false,
    });
    await handleAuthResponse(res);
  };

  const logIn = async (email: string, password: string) => {
    const res = await apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    await handleAuthResponse(res);
  };

  const logOut = async () => {
    try {
      await apiRequest("/auth/logout", { method: "POST" });
    } catch {
      // Best-effort server-side revocation — clear the local session either way.
    }
    await setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    const me = await apiRequest<User>("/auth/me");
    setUser(me);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, signUp, logIn, logOut, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
