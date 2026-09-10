"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Shield, UserRound } from "lucide-react";
import { getSystemHealth } from "@/lib/api";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, ErrorState, Skeleton } from "@/components/ui/primitives";
import { useAuth } from "@/lib/auth";
import type { SystemHealth } from "@/lib/types";

export default function SettingsPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHealth(await getSystemHealth());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load provider status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-secondary">Settings</h1>
        <p className="text-xs text-muted">Manage your account and check configured data sources.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><UserRound className="h-4 w-4" /> Account</CardTitle></CardHeader>
        <CardBody className="space-y-2 text-sm text-secondary">
          <p>{user?.name} · {user?.role}</p>
          <p>{user?.email}</p>
          <Link href="/profile" className="inline-block text-accent underline">Edit profile or change password</Link>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Shield className="h-4 w-4" /> Data sources</CardTitle>
          <Button onClick={load} disabled={loading}><RefreshCw className="h-4 w-4" /> Refresh status</Button>
        </CardHeader>
        <CardBody className="space-y-3">
          {error && <ErrorState message={error} onRetry={load} />}
          {loading && <Skeleton className="h-20 w-full" />}
          {!loading && !error && health && (
            <>
              <p className="text-xs text-muted">
                {health.demo_mode ? "Demo mode is enabled. Demo observations are not a training dataset." : "Demo mode is disabled. Missing sources remain unavailable."}
              </p>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                {health.components.map((provider) => (
                  <div key={provider.name} className="rounded border border-base-border p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm text-secondary">{provider.name}</p>
                      <Badge tone={provider.status === "operational" || provider.status === "online" ? "low" : "moderate"}>{provider.status}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted">{provider.mode} · {provider.detail}</p>
                  </div>
                ))}
              </div>
            </>
          )}
          <p className="text-xs text-muted">
            Data credentials and alert thresholds are managed by the project operator. Satellite catalog access does not provide verified burn-scar measurements. Changing a provider does not authorize model training.
          </p>
          <Link href="/system-health" className="inline-block text-sm text-accent underline">View system status</Link>
        </CardBody>
      </Card>
    </div>
  );
}
