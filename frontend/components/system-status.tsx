"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Activity, RefreshCw } from "lucide-react";
import { getSystemHealth } from "@/lib/api";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, ErrorState, Skeleton } from "@/components/ui/primitives";
import type { SystemHealth } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

const STATUS_TONE: Record<string, "low" | "moderate" | "high" | "critical" | "info" | "muted"> = {
  operational: "low",
  online: "low",
  demo: "moderate",
  baseline: "moderate",
  degraded: "high",
  offline: "critical",
  not_connected: "muted",
};

export function SystemStatusBar() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const fetchHealth = useCallback(() => {
    getSystemHealth().then(setHealth).catch(() => setHealth(null));
  }, []);
  useEffect(() => {
    fetchHealth();
    const t = setInterval(fetchHealth, 30000);
    return () => clearInterval(t);
  }, [fetchHealth]);

  return (
    <footer className="flex h-8 shrink-0 items-center justify-between border-t border-base-border/70 bg-base-panel/80 px-4">
      <div className="flex items-center gap-3 text-[10px] text-slate-500">
        <span className="flex items-center gap-1.5">
          <Activity className="h-3 w-3 text-accent" />
          System
        </span>
        {health ? (
          <span className={cn("font-semibold uppercase tracking-wider", health.overall === "operational" ? "text-low" : "text-moderate")}>
            {health.overall}
          </span>
        ) : (
          <span className="text-slate-600">connecting...</span>
        )}
      </div>
      <div className="hidden items-center gap-3 text-[10px] text-slate-500 sm:flex">
        {health?.components.slice(0, 4).map((c) => (
          <span key={c.name} className="flex items-center gap-1">
            <span className={cn("h-1.5 w-1.5 rounded-full", c.status === "operational" || c.status === "online" ? "bg-low" : c.status === "demo" || c.status === "baseline" ? "bg-moderate" : "bg-critical")} />
            {c.name.split(" ")[0]}
          </span>
        ))}
        {health && <span className="text-slate-600">updated {timeAgo(health.checked_at)}</span>}
      </div>
    </footer>
  );
}

export function SystemStatusPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getSystemHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 10 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }
  if (error) return <ErrorState message={`System health unavailable: ${error}`} onRetry={load} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">System Health</h1>
          <p className="text-xs text-slate-500">
            Overall status: <span className={cn("font-semibold uppercase", health?.overall === "operational" ? "text-low" : "text-moderate")}>{health?.overall}</span> · checked {health && timeAgo(health.checked_at)}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {health?.components.map((c) => {
          const ok = c.status === "operational" || c.status === "online";
          return (
            <Card key={c.name}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{c.name}</p>
                    <p className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-500">
                      {c.mode || "—"} · {c.latency_ms ? `${c.latency_ms} ms` : "n/a"}
                    </p>
                  </div>
                  <Badge tone={ok ? "low" : c.status === "demo" || c.status === "baseline" ? "moderate" : "critical"}>{c.status.toUpperCase()}</Badge>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-slate-600">{c.detail}</p>
                {c.last_sync && <p className="mt-1 text-[10px] text-slate-600">Last sync: {timeAgo(c.last_sync)}</p>}
              </CardBody>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Provider modes</CardTitle>
        </CardHeader>
        <CardBody className="text-xs text-slate-600">
          <p>
            All optional integrations degrade gracefully: when a live API key (FIRMS, satellite, Overpass) is unavailable the platform runs on seeded reference data. Configure keys in the backend{" "}
            <code className="rounded bg-base-raised px-1 py-0.5 text-sky-400">.env</code> to switch to live providers - the UI adapts automatically.
          </p>
          <Link href="/settings" className="mt-2 inline-block text-accent hover:underline">
            Open settings →
          </Link>
        </CardBody>
      </Card>
    </div>
  );
}