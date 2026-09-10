"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getMe, login as apiLogin, setToken } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  loginWithToken: (token: string) => Promise<User>;
  logout: () => void;
  hasRole: (min: "viewer" | "field" | "analyst" | "admin") => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const ROLE_LEVEL: Record<string, number> = { viewer: 1, field: 2, analyst: 3, admin: 4 };

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("firex_token");
    if (!token) {
      setLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const loginWithToken = useCallback(async (token: string) => {
    setToken(token);
    const me = await getMe();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    if (typeof window !== "undefined") window.location.href = "/login";
  }, []);

  const hasRole = useCallback(
    (min: "viewer" | "field" | "analyst" | "admin") => {
      if (!user) return false;
      return (ROLE_LEVEL[user.role] ?? 0) >= (ROLE_LEVEL[min] ?? 0);
    },
    [user]
  );

  return <AuthContext.Provider value={{ user, loading, login, loginWithToken, logout, hasRole }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}