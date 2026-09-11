"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, Flame, KeyRound, Loader2, MailCheck } from "lucide-react";
import { forgotPassword } from "@/lib/api";
import { Button, Input } from "@/components/ui/primitives";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg border border-base-border bg-base-panel">
            <Flame className="h-7 w-7 text-accent" strokeWidth={2.2} />
          </div>
          <h1 className="text-2xl font-bold tracking-widest text-primary">FIRE-X</h1>
          <p className="mt-1 text-xs uppercase tracking-[0.25em] text-muted/70">Password recovery</p>
        </div>

        <div className="rounded-lg border border-base-border bg-base-panel p-6 shadow-panel">
          {sent ? (
            <div className="py-4 text-center">
              <MailCheck className="mx-auto mb-3 h-10 w-10 text-low" />
              <p className="text-sm font-medium text-muted/30">Reset link sent</p>
              <p className="mt-1.5 text-xs leading-relaxed text-muted/70">
                If an account exists for <span className="font-mono text-muted/50">{email}</span>, a password-reset link is on its
                way. It expires in 30 minutes.
              </p>
              <p className="mt-2 text-[10px] text-muted">
                No SMTP configured? The email is written to the backend mail outbox instead - check the server console.
              </p>
              <Link href="/login" className="mt-4 inline-block text-xs text-accent hover:underline">
                Back to login
              </Link>
            </div>
          ) : (
            <form onSubmit={submit}>
              <p className="mb-4 text-xs leading-relaxed text-muted/70">
                Enter the email address linked to your FIRE-X account and we will send a one-time password-reset link.
              </p>
              <label className="mb-1.5 block text-xs font-medium text-muted/70" htmlFor="email">
                Email
              </label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />

              {error && (
                <p className="mt-3 rounded-md border border-critical/30 bg-critical/10 px-3 py-2 text-xs text-critical" role="alert">
                  {error}
                </p>
              )}

              <Button type="submit" disabled={busy || !email.trim()} className="mt-4 w-full">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
                Send reset link
              </Button>
            </form>
          )}
        </div>

        <Link href="/login" className="mt-4 flex items-center justify-center gap-1 text-xs text-muted/70 hover:text-muted/50">
          <ArrowLeft className="h-3 w-3" /> Back to login
        </Link>
      </div>
    </div>
  );
}