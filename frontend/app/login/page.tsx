"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, KeyRound, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { API_URL, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { user, login, loginWithToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [oauthBusy, setOauthBusy] = useState(false);

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  // Handle Google OAuth callback token: persist it AND update the auth context,
  // otherwise AppShell still sees user === null and bounces us back out.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (!token) return;
    // Strip the token from the address bar before doing anything else.
    window.history.replaceState({}, "", "/login");
    setOauthBusy(true);
    loginWithToken(token)
      .then(() => router.replace("/"))
      .catch(() => {
        setToken(null);
        setError("Google sign-in failed. Please try again.");
      })
      .finally(() => setOauthBusy(false));
  }, [loginWithToken, router]);

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
        setError("Google SSO is not configured on this server.");
      }
    } catch {
      setError("Could not connect to the server.");
    } finally {
      setGoogleLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-lg border border-base-border bg-base-raised/40 px-4 py-2.5 text-[13px] text-primary placeholder-muted/60 outline-none transition-colors focus:border-accent/60";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-base px-4 py-10">
      {/* Logo */}
      <Link href="/landing" className="mb-8 flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent">
          <Flame className="h-5 w-5 text-white" fill="currentColor" strokeWidth={2} />
        </div>
        <span className="text-[15px] font-semibold tracking-[0.18em] text-primary">FIRE-X</span>
      </Link>

      {/* Card */}
      <div className="w-full max-w-sm rounded-2xl border border-base-border bg-base-panel p-8 shadow-panel">
        <div className="mb-6">
          <h1 className="text-lg font-semibold text-primary">Welcome back</h1>
          <p className="mt-1 text-[13px] text-muted">
            {oauthBusy ? "Completing Google sign-in…" : "Sign in to access the command center"}
          </p>
        </div>

        {/* Google button */}          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={googleLoading || oauthBusy}
          className="mb-5 flex w-full items-center justify-center gap-3 rounded-lg border border-base-border bg-base px-4 py-2.5 text-[13px] font-medium text-secondary transition-colors hover:bg-base-raised disabled:opacity-50"
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
            <div className="w-full border-t border-base-border" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-base-panel px-3 text-[11px] text-muted">or sign in with email</span>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-secondary" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              placeholder="name@example.com"
              className={inputClass}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-secondary" htmlFor="password">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPw ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                placeholder="••••••••"
                className={`${inputClass} pr-10`}
              />
              <button
                type="button"
                onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted transition-colors hover:text-secondary"
                aria-label={showPw ? "Hide password" : "Show password"}
              >
                {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="flex justify-end">
            <Link href="/forgot-password" className="text-[11px] text-muted transition-colors hover:text-accent">
              Forgot password?
            </Link>
          </div>

          {error && (
            <div className="rounded-lg border border-critical/30 bg-critical/10 px-4 py-2.5 text-[12px] text-critical" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
            Sign in
          </button>
        </form>

        <p className="mt-6 text-center text-[12px] text-muted">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="font-medium text-accent transition-colors hover:underline">
            Sign up
          </Link>
        </p>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center">
        <p className="text-[10px] text-muted/70">Powered by NASA FIRMS · Scikit-learn · FastAPI · Next.js</p>
        <p className="mt-1 text-[9px] text-muted/50">© 2026 Team Pragya-X · Smart India Hackathon</p>
      </div>
    </div>
  );
}
