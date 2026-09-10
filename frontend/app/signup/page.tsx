"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, Loader2, UserPlus, Satellite, Brain, MapPin, BarChart3, Shield, Zap } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { signup as signupApi, setToken } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setBusy(true);
    try {
      const res = await signupApi(name, email, password);
      setToken(res.access_token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setBusy(false);
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
        <Link href="/landing" className="flex items-center gap-3 w-fit transition-opacity hover:opacity-80">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)", boxShadow: "0 0 30px rgba(14,165,233,0.3)" }}>
            <Flame className="h-6 w-6 text-white" strokeWidth={2.2} />
          </div>
          <div>
            <span className="text-lg font-bold tracking-[0.2em] text-white">FIRE-X</span>
            <span className="ml-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-sky-400">v1.0</span>
          </div>
        </Link>

        {/* Center hero */}
        <div className="max-w-xl">
          <div className="mb-6">
            <span className="inline-block rounded-full border border-sky-500/20 bg-sky-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-sky-400">
              SIH 2026 • PS 26162 • NTRO
            </span>
          </div>
          <h1 className="mb-4 text-[42px] font-extrabold leading-[1.1] tracking-tight text-white">
            Join the Next-Gen
            <br />
            <span style={{ background: "linear-gradient(135deg, #0ea5e9, #7c3aed, #f97316)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Intelligence Network
            </span>
          </h1>
          <p className="mb-8 max-w-md text-[15px] leading-relaxed text-slate-400">
            Create an account to access real-time thermal detection feeds, geospatial fire mapping, and AI-powered risk assessment tools.
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

      {/* Right side - Signup form */}
      <div className="relative flex w-full flex-col items-center justify-center px-6 py-10 lg:w-[480px] lg:px-12 xl:w-[520px]">
        {/* Glass panel background */}
        <div className="absolute inset-0 border-l border-white/[0.06]" style={{ background: "rgba(8, 12, 24, 0.8)", backdropFilter: "blur(20px)" }} />

        <div className="relative w-full max-w-sm">
          {/* Mobile logo (hidden on desktop) */}
          <div className="mb-8 text-center lg:hidden">
            <Link href="/landing" className="inline-block">
              <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)", boxShadow: "0 0 30px rgba(14,165,233,0.3)" }}>
                <Flame className="h-7 w-7 text-white" strokeWidth={2.2} />
              </div>
            </Link>
            <h1 className="text-xl font-bold tracking-[0.2em] text-white">FIRE-X</h1>
            <p className="mt-1 text-[10px] uppercase tracking-[0.25em] text-sky-400/70">Create Account</p>
          </div>

          {/* Welcome text */}
          <div className="mb-7">
            <h2 className="text-xl font-bold text-white">Create your account</h2>
            <p className="mt-1 text-[13px] text-slate-500">Join FIRE-X to access the command center</p>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="name">Full Name</label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="John Doe"
                minLength={2}
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20"
              />
            </div>
            
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
                  required
                  placeholder="Min. 6 characters"
                  minLength={6}
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

            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="confirm">Confirm Password</label>
              <input
                id="confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-[12px] text-red-400" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-[13px] font-semibold text-white transition-all duration-200 hover:shadow-lg disabled:opacity-50"
              style={{
                background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)",
                boxShadow: "0 4px 20px rgba(14,165,233,0.25)",
              }}
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              Create Account
            </button>
          </form>

          <p className="mt-5 text-center text-[12px] text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-sky-400 transition-colors hover:text-sky-300">Sign in</Link>
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
