"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, KeyRound, Loader2, MapPin, Shield, Zap, BarChart3, Satellite, Brain } from "lucide-react";
import { useAuth } from "@/lib/auth";
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

  // Handle Google OAuth callback token
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
        setError("Google SSO is not configured on this server.");
      }
    } catch {
      setError("Could not connect to the server.");
    } finally {
      setGoogleLoading(false);
    }
  };

  const features = [
    { icon: Satellite, label: "NASA FIRMS Integration", desc: "Real-time satellite thermal detection" },
    { icon: Brain, label: "AI Classification", desc: "HistGradientBoosting ML engine" },
    { icon: MapPin, label: "GIS Dashboard", desc: "Interactive geospatial mapping" },
    { icon: BarChart3, label: "Risk Analytics", desc: "Predictive risk scoring" },
    { icon: Shield, label: "Alert System", desc: "Multi-channel incident alerts" },
    { icon: Zap, label: "Real-time SSE", desc: "Live event streaming" },
  ];

  return (
    <div className="relative flex min-h-screen overflow-hidden" style={{ background: "#020408" }}>
      {/* Animated background effects */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-[600px] w-[600px] rounded-full opacity-[0.07]" style={{ background: "radial-gradient(circle, #0ea5e9, transparent 70%)" }} />
        <div className="absolute -bottom-60 -right-60 h-[700px] w-[700px] rounded-full opacity-[0.05]" style={{ background: "radial-gradient(circle, #7c3aed, transparent 70%)" }} />
        <div className="absolute left-1/2 top-1/3 h-[400px] w-[400px] -translate-x-1/2 rounded-full opacity-[0.03]" style={{ background: "radial-gradient(circle, #f97316, transparent 70%)" }} />
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.04]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)", backgroundSize: "60px 60px" }} />
      </div>

      {/* Left side - Landing / Hero */}
      <div className="relative hidden flex-1 flex-col justify-between p-10 lg:flex xl:p-14">
        {/* Top logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)", boxShadow: "0 0 30px rgba(14,165,233,0.3)" }}>
            <Flame className="h-6 w-6 text-white" strokeWidth={2.2} />
          </div>
          <div>
            <span className="text-lg font-bold tracking-[0.2em] text-white">FIRE-X</span>
            <span className="ml-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-sky-400">v1.0</span>
          </div>
        </div>

        {/* Center hero */}
        <div className="max-w-xl">
          <div className="mb-6">
            <span className="inline-block rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-sky-400">
              SIH 2026 • PS 26162 • NTRO
            </span>
          </div>
          <h1 className="mb-4 text-[42px] font-extrabold leading-[1.1] tracking-tight text-white">
            AI-Powered Fire
            <br />
            <span style={{ background: "linear-gradient(135deg, #0ea5e9, #7c3aed, #f97316)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Intelligence Platform
            </span>
          </h1>
          <p className="mb-8 max-w-md text-[15px] leading-relaxed text-slate-400">
            Detect, classify, and respond to industrial fires and thermal anomalies using NASA FIRMS satellite data, 
            geospatial AI, and real-time risk analytics.
          </p>

          {/* Feature grid */}
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
            {features.map((f, i) => (
              <div
                key={i}
                className="group rounded-xl border border-white/[0.06] p-3 transition-all duration-300 hover:border-sky-500/20 hover:bg-white/[0.02]"
                style={{ backdropFilter: "blur(8px)" }}
              >
                <f.icon className="mb-2 h-4 w-4 text-sky-400 transition-transform group-hover:scale-110" />
                <p className="text-[12px] font-semibold text-slate-200">{f.label}</p>
                <p className="text-[10px] text-slate-500">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom stats */}
        <div className="flex items-center gap-8">
          <div>
            <p className="text-2xl font-bold text-white">50K+</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Daily Detections</p>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div>
            <p className="text-2xl font-bold text-white">&lt;2ms</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Inference Time</p>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div>
            <p className="text-2xl font-bold text-white">95%+</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Accuracy</p>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div>
            <p className="text-2xl font-bold text-white">24/7</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Monitoring</p>
          </div>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="relative flex w-full flex-col items-center justify-center px-6 py-10 lg:w-[480px] lg:px-12 xl:w-[520px]">
        {/* Glass panel background */}
        <div className="absolute inset-0 border-l border-white/[0.06]" style={{ background: "rgba(8, 12, 24, 0.8)", backdropFilter: "blur(20px)" }} />

        <div className="relative w-full max-w-sm">
          {/* Mobile logo (hidden on desktop) */}
          <div className="mb-8 text-center lg:hidden">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)", boxShadow: "0 0 30px rgba(14,165,233,0.3)" }}>
              <Flame className="h-7 w-7 text-white" strokeWidth={2.2} />
            </div>
            <h1 className="text-xl font-bold tracking-[0.2em] text-white">FIRE-X</h1>
            <p className="mt-1 text-[10px] uppercase tracking-[0.25em] text-sky-400/70">AI Fire Intelligence</p>
          </div>

          {/* Welcome text */}
          <div className="mb-7">
            <h2 className="text-xl font-bold text-white">Welcome back</h2>
            <p className="mt-1 text-[13px] text-slate-500">Sign in to access the command center</p>
          </div>

          {/* Google button */}
          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={googleLoading}
            className="mb-5 flex w-full items-center justify-center gap-3 rounded-xl border border-white/[0.08] py-2.5 text-[13px] font-medium text-slate-300 transition-all duration-200 hover:border-white/[0.15] hover:bg-white/[0.04] disabled:opacity-50"
            style={{ background: "rgba(255,255,255,0.03)" }}
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
              <div className="w-full border-t border-white/[0.06]" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 text-[11px] text-slate-600" style={{ background: "rgba(8, 12, 24, 0.8)" }}>or sign in with email</span>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                placeholder="name@example.com"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 pr-10 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 transition-colors hover:text-slate-400"
                  aria-label={showPw ? "Hide password" : "Show password"}
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <Link href="/forgot-password" className="text-[11px] text-slate-500 transition-colors hover:text-sky-400">
                Forgot password?
              </Link>
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-[12px] text-red-400" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-[13px] font-semibold text-white transition-all duration-200 hover:shadow-lg disabled:opacity-50"
              style={{
                background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)",
                boxShadow: "0 4px 20px rgba(14,165,233,0.25)",
              }}
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
              Sign In
            </button>
          </form>

          <p className="mt-5 text-center text-[12px] text-slate-500">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="font-medium text-sky-400 transition-colors hover:text-sky-300">Sign up</Link>
          </p>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-[10px] text-slate-600">
              Powered by NASA FIRMS · Scikit-learn · FastAPI · Next.js
            </p>
            <p className="mt-1 text-[9px] text-slate-700">
              © 2026 Team Pragya-X · Smart India Hackathon
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}