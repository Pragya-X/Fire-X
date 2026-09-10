"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, Loader2, UserPlus } from "lucide-react";
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

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10" style={{ background: "#020408" }}>
      {/* Background effects */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-[600px] w-[600px] rounded-full opacity-[0.07]" style={{ background: "radial-gradient(circle, #7c3aed, transparent 70%)" }} />
        <div className="absolute -bottom-60 -right-60 h-[700px] w-[700px] rounded-full opacity-[0.05]" style={{ background: "radial-gradient(circle, #0ea5e9, transparent 70%)" }} />
        <div className="absolute inset-0 opacity-[0.04]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)", backgroundSize: "60px 60px" }} />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <Link href="/landing" className="inline-block">
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)", boxShadow: "0 0 30px rgba(14,165,233,0.3)" }}>
              <Flame className="h-7 w-7 text-white" strokeWidth={2.2} />
            </div>
          </Link>
          <h1 className="text-xl font-bold tracking-[0.2em] text-white">FIRE-X</h1>
          <p className="mt-1 text-[10px] uppercase tracking-[0.25em] text-sky-400/70">Create your account</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-white/[0.06] p-7" style={{ background: "rgba(8, 12, 24, 0.8)", backdropFilter: "blur(20px)" }}>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="name">Full Name</label>
              <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="John Doe" minLength={2}
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20" />
            </div>
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="email">Email address</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="name@example.com"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20" />
            </div>
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="password">Password</label>
              <div className="relative">
                <input id="password" type={showPw ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Min. 6 characters" minLength={6}
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 pr-10 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400">
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-[12px] font-medium text-slate-400" htmlFor="confirm">Confirm Password</label>
              <input id="confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required placeholder="••••••••"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-[13px] text-white placeholder-slate-600 outline-none transition-all duration-200 focus:border-sky-500/40 focus:ring-1 focus:ring-sky-500/20" />
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-[12px] text-red-400">{error}</div>
            )}

            <button type="submit" disabled={busy}
              className="flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-[13px] font-semibold text-white transition-all duration-200 hover:shadow-lg disabled:opacity-50"
              style={{ background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)", boxShadow: "0 4px 20px rgba(14,165,233,0.25)" }}>
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              Create Account
            </button>
          </form>

          <p className="mt-5 text-center text-[12px] text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-sky-400 transition-colors hover:text-sky-300">Sign in</Link>
          </p>
        </div>

        <p className="mt-6 text-center text-[9px] text-slate-700">© 2026 Team Pragya-X · Smart India Hackathon</p>
      </div>
    </div>
  );
}
