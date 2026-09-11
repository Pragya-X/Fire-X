"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, Loader2, UserPlus, Satellite, Brain, MapPin, BarChart3 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { signup as signupApi, setToken } from "@/lib/api";

const POINTS = [
  { icon: Satellite, title: "Live NASA FIRMS feed", desc: "Thermal detections synced every 2 minutes" },
  { icon: Brain, title: "Explainable AI classification", desc: "SHAP-backed decisions with confidence scores" },
  { icon: MapPin, title: "GIS command center", desc: "Interactive hotspot mapping with zone overlays" },
  { icon: BarChart3, title: "Risk analytics", desc: "Multi-factor scoring with persistence patterns" },
];

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
            Join the fire<br />
            <span className="text-sky-400">intelligence network.</span>
          </h1>
          <p className="mb-10 max-w-md text-[14px] leading-relaxed text-slate-400">
            Create an account to access live satellite feeds, geospatial fire mapping, and
            AI-powered risk assessment tools.
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {POINTS.map((p) => (
              <div key={p.title} className="rounded-xl border border-white/10 bg-white/[0.04] p-3.5">
                <p.icon className="mb-2 h-4 w-4 text-sky-400" strokeWidth={1.9} />
                <p className="text-[12.5px] font-semibold text-white">{p.title}</p>
                <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-[11px] text-slate-500">
          SIH 2026 · PS 26162 · NTRO · © 2026 Team Pragya-X
        </p>
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
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">Create your account</h2>
            <p className="mt-1.5 text-[13px] text-slate-500">Join FIRE-X to access the command center</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-700" htmlFor="name">
                Full name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                minLength={2}
                placeholder="John Doe"
                className={inputClass}
              />
            </div>

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
              <label className="mb-1.5 block text-[12px] font-medium text-slate-700" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  placeholder="Min. 6 characters"
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

            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-700" htmlFor="confirm">
                Confirm password
              </label>
              <input
                id="confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                placeholder="Re-enter password"
                className={inputClass}
              />
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
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              Create account
            </button>
          </form>

          <p className="mt-6 text-center text-[13px] text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-accent hover:underline">
              Sign in
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
