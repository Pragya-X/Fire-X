"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, KeyRound, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Button, Input } from "@/components/ui/primitives";
import { API_URL } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  // Handle Google OAuth callback token in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      import("@/lib/api").then(({ setToken, getMe }) => {
        setToken(token);
        getMe()
          .then(() => router.replace("/"))
          .catch(() => {
            setToken(null);
            setError("Google sign-in failed. Please try again.");
          });
      });
    }
  }, [router]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/google/login`);
      const data = await res.json();
      if (data.configured && data.authorize_url) {
        window.location.href = data.authorize_url;
      } else {
        setError("Google SSO is not configured on this server. Please use email login.");
      }
    } catch {
      setError("Could not connect to the server. Is the backend running?");
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4" style={{ background: "linear-gradient(135deg, #04070d 0%, #07101f 100%)" }}>
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
            style={{ background: "linear-gradient(135deg, #0284c7 0%, #7c3aed 100%)", boxShadow: "0 0 32px rgba(2,132,199,0.4)" }}
          >
            <Flame className="h-8 w-8 text-white" strokeWidth={2.2} />
          </div>
          <h1 className="text-2xl font-bold tracking-widest text-white">FIRE-X</h1>
          <p className="mt-1 text-[11px] uppercase tracking-[0.25em] text-sky-400/70">AI-Powered Geospatial Fire Intelligence</p>
          <p className="mt-1.5 text-[11px] text-muted/60">Detect · Classify · Understand · Respond</p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl border border-base-border/60 p-7 shadow-2xl"
          style={{ background: "rgba(10, 16, 28, 0.85)", backdropFilter: "blur(12px)" }}
        >
          {/* Google button */}
          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={googleLoading}
            className="mb-5 flex w-full items-center justify-center gap-3 rounded-xl border border-base-border/70 bg-base-raised/40 py-2.5 text-sm font-medium text-primary transition-all hover:border-accent/40 hover:bg-base-raised/80 disabled:opacity-60"
          >
            {googleLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <svg className="h-4 w-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
            )}
            Continue with Google
          </button>

          {/* Divider */}
          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-base-border/40" />
            </div>
            <div className="relative flex justify-center text-[11px]">
              <span className="bg-[#0a101c] px-3 text-muted/50">or sign in with email</span>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted/70" htmlFor="email">Email</label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required placeholder="your@email.com" />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted/70" htmlFor="password">Password</label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted/50 hover:text-muted"
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <Link href="/forgot-password" className="text-[11px] text-muted/60 hover:text-accent transition-colors">
                Forgot password?
              </Link>
            </div>

            {error && (
              <p className="rounded-lg border border-critical/30 bg-critical/10 px-3 py-2 text-xs text-critical" role="alert">
                {error}
              </p>
            )}

            <Button type="submit" disabled={busy} className="w-full" size="lg">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
              Sign In
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}