"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, KeyRound, Loader2, ShieldCheck, Satellite, Brain, Bell } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { API_URL, setToken } from "@/lib/api";

const HIGHLIGHTS = [
  { icon: Satellite, title: "Live NASA FIRMS feed", desc: "Thermal detections synced every 2 minutes" },
  { icon: Brain, title: "Explainable AI classification", desc: "SHAP-backed decisions with confidence scores" },
  { icon: Bell, title: "Instant multi-channel alerts", desc: "SSE streaming, notifications, and email" },
];

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

  // Handle Google OAuth callback: the backend redirects back with a one-time
  // code (never a raw token). Redeem it for a session, then clean the URL.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    if (!code) return;
    // Strip the code from the address bar before doing anything else.
    window.history.replaceState({}, "", "/login");
    setOauthBusy(true);
    fetch(`${API_URL}/api/v1/auth/google/exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Exchange failed");
        return res.json();
      })
      .then((data) => loginWithToken(data.access_token))
      .then(() => router.replace("/"))
      .catch(() => {
        setError("Google sign-in failed or the link expired. Please try again.");
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
      const res = await fetch(`${API_URL}/api/v1/auth/google/login`, { credentials: "include" });
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
    "w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-[13px] text-slate-900 placeholder-slate-400 outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent/15";

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left brand panel */}
      <div className="relative hidden w-[46%] flex-col justify-between overflow-hidden bg-slate-900 p-10 text-white xl:p-14 lg:flex">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 15%, rgba(14,165,233,0.22), transparent 45%), radial-gradient(circle at 85% 85%, rgba(6,182,212,0.16), transparent 45%)",
          }}
        />
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        <Link href="/landing" className="relative flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500 to-cyan-500 shadow-lg shadow-sky-500/30">
            <Flame className="h-5 w-5 text-white" fill="currentColor" strokeWidth={2} />
          </div>
          <div>
            <span className="block text-[15px] font-bold leading-tight tracking-[0.14em]">FIRE-X</span>
            <span className="block text-[10px] leading-tight text-slate-400">AI Fire Intelligence</span>
          </div>
        </Link>

        <div className="relative">
          <h1 className="mb-4 max-w-md text-3xl font-bold leading-tight tracking-tight">
            Fire intelligence<br />
            <span className="text-sky-400">you can act on.</span>
          </h1>
          <p className="mb-10 max-w-md text-[14px] leading-relaxed text-slate-400">
            Real-time detection, AI classification, and incident response for India&apos;s
            industrial landscape — powered by NASA satellites.
          </p>

          <div className="space-y-4">
            {HIGHLIGHTS.map((h) => (
              <div key={h.title} className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <h.icon className="h-4 w-4 text-sky-400" strokeWidth={1.9} />
                </div>
                <div>
                  <p className="text-[13px] font-semibold text-white">{h.title}</p>
                  <p className="text-[12px] text-slate-400">{h.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative flex items-center gap-6 text-[11px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> SIH 2026 · PS 26162 · NTRO
          </span>
          <span>© 2026 Team Pragya-X</span>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-10 lg:w-[54%]">
        <div className="w-full max-w-[400px]">
          {/* Mobile brand */}
          <Link href="/landing" className="mb-8 flex items-center justify-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent">
              <Flame className="h-5 w-5 text-white" fill="currentColor" strokeWidth={2} />
            </div>
            <span className="text-[15px] font-bold tracking-[0.14em] text-slate-900">FIRE-X</span>
          </Link>

          <div className="mb-7">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              {oauthBusy ? "Completing sign-in…" : "Sign in to FIRE-X"}
            </h2>
            <p className="mt-1.5 text-[13px] text-slate-500">
              {oauthBusy ? "Verifying your Google account" : "Access the fire intelligence command center"}
            </p>
          </div>

          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={googleLoading || oauthBusy}
            className="mb-5 flex w-full items-center justify-center gap-3 rounded-lg border border-slate-300 bg-white py-2.5 text-[13px] font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
          >
            {googleLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
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

          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-[11px] text-slate-400">or sign in with email</span>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-700" htmlFor="email">
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
              <div className="mb-1.5 flex items-center justify-between">
                <label className="block text-[12px] font-medium text-slate-700" htmlFor="password">
                  Password
                </label>
                <Link href="/forgot-password" className="text-[11px] font-medium text-accent hover:underline">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  placeholder="Enter your password"
                  className={`${inputClass} pr-10`}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-600"
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-[12px] text-red-700" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-2.5 text-[13px] font-semibold text-white shadow-sm transition-colors hover:bg-accent/90 disabled:opacity-50"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
              Sign in
            </button>
          </form>

          <p className="mt-6 text-center text-[13px] text-slate-500">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="font-semibold text-accent hover:underline">
              Create one
            </Link>
          </p>

          <p className="mt-10 text-center text-[10px] text-slate-400">
            Powered by NASA FIRMS · Scikit-learn · FastAPI · Next.js
          </p>
        </div>
      </div>
    </div>
  );
}
