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
          <h1 className="text-lg font-semibold text-primary">Create your account</h1>
          <p className="mt-1 text-[13px] text-muted">Join FIRE-X to access the command center</p>
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-secondary" htmlFor="name">
              Full name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="John Doe"
              minLength={2}
              className={inputClass}
            />
          </div>

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
                required
                placeholder="Min. 6 characters"
                minLength={6}
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

          <div>
            <label className="mb-1.5 block text-[12px] font-medium text-secondary" htmlFor="confirm">
              Confirm password
            </label>
            <input
              id="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              placeholder="••••••••"
              className={inputClass}
            />
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
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
            Create account
          </button>
        </form>

        <p className="mt-6 text-center text-[12px] text-muted">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-accent transition-colors hover:underline">
            Sign in
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
