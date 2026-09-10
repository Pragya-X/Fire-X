"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Eye, EyeOff, Flame, KeyRound, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Button, Input } from "@/components/ui/primitives";

const ADMIN_EMAIL = "npgearly@gmail.com";
const ADMIN_PASSWORD = "admin123";

export default function LoginPage() {
  const router = useRouter();
  const { user, login } = useAuth();
  const [email, setEmail] = useState(ADMIN_EMAIL);
  const [password, setPassword] = useState(ADMIN_PASSWORD);
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

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

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg border border-base-border bg-slate-800">
            <Flame className="h-7 w-7 text-accent" strokeWidth={2.2} />
          </div>
          <h1 className="text-2xl font-bold tracking-widest text-white">FIRE-X</h1>
          <p className="mt-1 text-xs uppercase tracking-[0.25em] text-slate-400">AI-Powered Geospatial Fire Intelligence</p>
          <p className="mt-2 text-[11px] text-slate-600">Detect. Classify. Understand. Respond.</p>
        </div>

        <form onSubmit={submit} className="rounded-lg border border-base-border bg-base-panel p-6 shadow-panel">
          <label className="mb-1.5 block text-xs font-medium text-slate-400" htmlFor="email">
            Email
          </label>
          <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />

          <label className="mb-1.5 mt-4 block text-xs font-medium text-slate-400" htmlFor="password">
            Password
          </label>
          <div className="relative">
            <Input id="password" type={showPw ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
            <button
              type="button"
              onClick={() => setShowPw(!showPw)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-300"
              aria-label={showPw ? "Hide password" : "Show password"}
            >
              {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          <div className="mt-2 flex justify-end">
            <Link href="/forgot-password" className="text-[11px] text-slate-400 hover:text-accent">
              Forgot password?
            </Link>
          </div>

          {error && (
            <p className="mt-3 rounded-md border border-critical/30 bg-critical/10 px-3 py-2 text-xs text-critical" role="alert">
              {error}
            </p>
          )}

          <Button type="submit" disabled={busy} className="mt-5 w-full" size="lg">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
            Access Command Center
          </Button>
        </form>
      </div>
    </div>
  );
}