"use client";

import { useCallback, useEffect, useState } from "react";
import { CalendarDays, KeyRound, Loader2, Lock, Mail, Shield, UserRound } from "lucide-react";
import { changePassword, getActivity } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, ErrorState, Input, Skeleton, useToast } from "@/components/ui/primitives";
import type { ActivityItem } from "@/lib/types";
import { timeAgo } from "@/lib/utils";

const ROLE_TONE: Record<string, "low" | "info" | "purple" | "critical" | "muted"> = {
  admin: "critical",
  analyst: "info",
  field: "purple",
  viewer: "muted",
};

export default function ProfilePage() {
  const { user } = useAuth();
  const { push } = useToast();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changing, setChanging] = useState(false);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(true);
  const [activityError, setActivityError] = useState<string | null>(null);

  const loadActivity = useCallback(() => {
    setLoadingActivity(true);
    setActivityError(null);
    getActivity()
      .then((r) => setActivity(r.items as ActivityItem[]))
      .catch((e: Error) => setActivityError(e.message))
      .finally(() => setLoadingActivity(false));
  }, []);

  useEffect(loadActivity, [loadActivity]);

  const submitPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      push({ title: "Password too short", message: "New password must be at least 6 characters.", tone: "error" });
      return;
    }
    if (newPassword !== confirmPassword) {
      push({ title: "Passwords do not match", message: "New password and confirmation differ.", tone: "error" });
      return;
    }
    setChanging(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      push({ title: "Password updated", message: "Your password has been changed.", tone: "success" });
      loadActivity();
    } catch (err) {
      push({ title: "Password change failed", message: err instanceof Error ? err.message : "Could not update password", tone: "error" });
    } finally {
      setChanging(false);
    }
  };

  if (!user) return null;

  const initials = user.name
    .split(/\s+/)
    .map((p) => p.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-slate-700">Profile</h1>
        <p className="text-xs text-slate-400">Account details, security and recent activity</p>
      </div>

      <Card>
        <CardBody>
          <div className="flex flex-wrap items-center gap-4">
            <span className="flex h-14 w-14 items-center justify-center rounded-full border border-base-border bg-base-panel text-lg font-bold text-accent">
              {initials}
            </span>
            <div className="min-w-0">
              <p className="text-base font-semibold text-slate-700">{user.name}</p>
              <p className="flex items-center gap-1.5 text-xs text-slate-600">
                <Mail className="h-3 w-3" /> {user.email}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <Badge tone={ROLE_TONE[user.role] ?? "muted"}>
                <Shield className="h-3 w-3" /> {user.role.toUpperCase()}
              </Badge>
              {user.created_at && (
                <span className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <CalendarDays className="h-3.5 w-3.5" /> Member since {new Date(user.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                </span>
              )}
            </div>
          </div>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <UserRound className="h-4 w-4 text-accent" /> Account details
            </CardTitle>
          </CardHeader>
          <CardBody className="space-y-2.5 text-sm">
            <div className="flex items-center justify-between border-b border-base-border/40 pb-2">
              <span className="text-xs text-slate-400">Name</span>
              <span className="text-slate-700">{user.name}</span>
            </div>
            <div className="flex items-center justify-between border-b border-base-border/40 pb-2">
              <span className="text-xs text-slate-400">Email</span>
              <span className="font-mono text-xs text-slate-700">{user.email}</span>
            </div>
            <div className="flex items-center justify-between border-b border-base-border/40 pb-2">
              <span className="text-xs text-slate-400">Role</span>
              <span className="text-xs text-slate-700">{user.role}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Account ID</span>
              <span className="font-mono text-xs text-slate-700">#{user.id}</span>
            </div>
            <p className="pt-1 text-[10px] text-slate-400">
              Permissions: viewer = view · field = update alerts · analyst = analyze/ingest · admin = everything.
            </p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <KeyRound className="h-4 w-4 text-accent" /> Change password
            </CardTitle>
          </CardHeader>
          <CardBody>
            <form onSubmit={submitPassword} className="space-y-3">
              <label className="block">
                <span className="mb-1 block text-xs text-slate-600">Current password</span>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                  <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="pl-9" required autoComplete="current-password" />
                </div>
              </label>
              <label className="block">
                <span className="mb-1 block text-xs text-slate-600">New password</span>
                <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required autoComplete="new-password" />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs text-slate-600">Confirm new password</span>
                <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required autoComplete="new-password" />
              </label>
              <Button type="submit" disabled={changing}>
                {changing ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
                Update password
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
          <span className="text-[10px] uppercase tracking-wider text-slate-600">audit log</span>
        </CardHeader>
        <CardBody>
          {loadingActivity && <Skeleton className="h-24" />}
          {activityError && <ErrorState message={`Activity log unavailable: ${activityError}`} onRetry={loadActivity} />}
          {!loadingActivity && !activityError && activity.length === 0 && (
            <p className="py-6 text-center text-xs text-slate-400">No recorded activity yet.</p>
          )}
          <ul className="divide-y divide-base-border/50">
            {activity.slice(0, 20).map((a) => (
              <li key={a.id} className="flex items-center gap-3 py-2">
                <span className="font-mono text-[10px] text-slate-600">{timeAgo(a.created_at)}</span>
                <span className="rounded border border-base-border/60 bg-base-raised/50 px-1.5 py-0.5 text-[10px] font-medium text-slate-700">
                  {a.action.replace(/_/g, " ")}
                </span>
                <span className="text-[11px] text-slate-600">{a.entity}</span>
                <span className="ml-auto font-mono text-[10px] text-slate-400">{a.user}</span>
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>
    </div>
  );
}