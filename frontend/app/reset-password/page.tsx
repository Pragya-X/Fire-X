"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Flame, KeyRound, Loader2 } from "lucide-react";
import { resetPassword } from "@/lib/api";
import { Button, Input } from "@/components/ui/primitives";

function ResetPasswordInner() {
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
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
          <p className="mt-1 text-xs uppercase tracking-[0.25em] text-muted/70">Choose a new password</p>
        </div>

        <div className="rounded-lg border border-base-border bg-base-panel p-6 shadow-panel">
          {!token ? (
            <div className="py-4 text-center">
              <p className="text-sm text-muted/50">This reset link is missing its token.</p>
              <p className="mt-1 text-xs text-muted/70">Use the link from the password-reset email, or request a new one.</p>
              <Link href="/forgot-password" className="mt-4 inline-block text-xs text-accent hover:underline">
                Request a new link
              </Link>
            </div>
          ) : done ? (
            <div className="py-4 text-center">
              <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-low" />
              <p className="text-sm font-medium text-muted/30">Password updated</p>
              <p className="mt-1.5 text-xs text-muted/70">Sign in with your new password.</p>
              <Link href="/login" className="mt-4 inline-block text-xs text-accent hover:underline">
                Go to login
              </Link>
            </div>
          ) : (
            <form onSubmit={submit}>
              <label className="mb-1.5 block text-xs font-medium text-muted/70" htmlFor="password">
                New password
              </label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />

              <label className="mb-1.5 mt-4 block text-xs font-medium text-muted/70" htmlFor="confirm">
                Confirm new password
              </label>
              <Input id="confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required />

              {error && (
                <p className="mt-3 rounded-md border border-critical/30 bg-critical/10 px-3 py-2 text-xs text-critical" role="alert">
                  {error}
                </p>
              )}

              <Button type="submit" disabled={busy || !password || !confirm} className="mt-5 w-full">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
                Update password
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted/70" /></div>}>
      <ResetPasswordInner />
    </Suspense>
  );
}