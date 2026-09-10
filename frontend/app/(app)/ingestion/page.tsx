"use client";

import { useCallback, useEffect, useState } from "react";
import { CloudDownload, Database, Loader2, Map, RefreshCw, Satellite, Sparkles, Cpu } from "lucide-react";
import { getActivity, getSystemHealth, ingestDemo, ingestFirms, ingestLandcover, ingestOsm, recalculateRisk, refreshAnalysis } from "@/lib/api";
import type { IngestResult } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, Skeleton, useToast } from "@/components/ui/primitives";
import { useAuth } from "@/lib/auth";
import { timeAgo } from "@/lib/utils";

interface SyncRow {
  id: number;
  action: string;
  entity: string;
  user: string;
  created_at: string;
  details: Record<string, unknown>;
}

export default function IngestionPage() {
  const { push } = useToast();
  const { hasRole } = useAuth();
  const [activity, setActivity] = useState<SyncRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [results, setResults] = useState<Record<string, IngestResult | { updated: number; duration_ms: number }>>({});

  const load = useCallback(() => {
    getActivity().then((r) => setActivity(r.items as SyncRow[])).catch(() => undefined);
    getSystemHealth().then((health) => setDemoMode(health.demo_mode)).catch(() => setDemoMode(false));
  }, []);
  useEffect(load, [load]);

  const run = async (key: string, fn: () => Promise<unknown>) => {
    setBusy(key);
    try {
      const res = await fn();
      setResults((prev) => ({ ...prev, [key]: res as never }));
      push({ title: `${key} completed`, message: "Operation finished successfully.", tone: "success" });
      load();
    } catch (e) {
      push({ title: `${key} failed`, message: e instanceof Error ? e.message : "Operation failed", tone: "error" });
    } finally {
      setBusy(null);
    }
  };

  const actions = [
    { key: "firms", label: "Sync Live NASA Data", desc: "Pull real-time thermal anomalies from NASA FIRMS", icon: <Satellite className="h-4 w-4" />, fn: () => run("firms", ingestFirms), allowed: true },
    { key: "demo", label: "Sync demo batch", desc: "Generate a demonstration detection batch", icon: <CloudDownload className="h-4 w-4" />, fn: () => run("demo", ingestDemo), allowed: demoMode },
    { key: "osm", label: "Sync OSM", desc: "Fetch OpenStreetMap infrastructure; seeded fallback requires demo mode", icon: <Map className="h-4 w-4" />, fn: () => run("osm", ingestOsm), allowed: true },
    { key: "landcover", label: "Preview demo land cover", desc: "Read seeded polygons; does not install real references", icon: <Database className="h-4 w-4" />, fn: () => run("landcover", ingestLandcover), allowed: demoMode },
    { key: "refresh", label: "Refresh Analysis", desc: "Re-run temporal + classification + risk on all hotspots", icon: <RefreshCw className="h-4 w-4" />, fn: () => run("refresh", refreshAnalysis), allowed: true },
    { key: "risk", label: "Recalculate Risk", desc: "Recompute risk scores for every detection", icon: <Sparkles className="h-4 w-4" />, fn: () => run("risk", recalculateRisk), allowed: true },
  ];

  const canIngest = hasRole("analyst");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-secondary">Data Ingestion</h1>
          <p className="text-xs text-muted/70">Provider status is reported for each operation. Real training references must be supplied through the documented reference bundle workflow.</p>
        </div>
        <Badge tone={canIngest ? "info" : "muted"}>{canIngest ? "ANALYST ACCESS" : "VIEW ONLY"}</Badge>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {actions.filter((a) => a.allowed).map((a) => {
          const res = results[a.key];
          const isLoading = busy === a.key;
          return (
            <Card key={a.key}>
              <CardBody>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md border border-base-border bg-base-raised p-2 text-accent">{a.icon}</span>
                    <div>
                      <p className="text-sm font-semibold text-secondary">{a.label}</p>
                      <p className="mt-0.5 text-[10px] text-muted/70">{a.desc}</p>
                    </div>
                  </div>
                  <Cpu className="h-3.5 w-3.5 text-muted" />
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <Button size="sm" variant={a.key === "demo" ? "default" : "outline"} onClick={a.fn} disabled={isLoading || !canIngest}>
                    {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
                    {isLoading ? "Running..." : a.label}
                  </Button>
                  {res && (
                    <span className="text-[10px] text-muted/70">
                      {"duration_ms" in res ? `${res.duration_ms} ms` : ""}
                    </span>
                  )}
                </div>
                {res && "mode" in res && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    <Badge tone={res.mode === "live" ? "low" : "moderate"}>{res.mode.toUpperCase()} MODE</Badge>
                    {"hotspots_created" in res && <Badge tone="info">+{res.hotspots_created} created</Badge>}
                    {"alerts_created" in res && res.alerts_created > 0 && <Badge tone="critical">+{res.alerts_created} alerts</Badge>}
                  </div>
                )}
                {res && "updated" in res && (
                  <div className="mt-2 flex gap-1.5">
                    <Badge tone="info">{res.updated} hotspots analyzed</Badge>
                  </div>
                )}
                {res && "errors" in res && (res.errors as string[]).length > 0 && (
                  <p className="mt-2 text-[10px] text-moderate">{String((res.errors as string[])[0])}</p>
                )}
              </CardBody>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader><CardTitle>Activity log</CardTitle></CardHeader>
        <CardBody className="p-0">
          {activity.length === 0 ? <Skeleton className="m-4 h-32" /> : (
            <table className="w-full text-left text-xs">
              <thead className="border-b border-base-border/70 text-muted/70">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Time</th>
                  <th className="px-4 py-2.5 font-medium">User</th>
                  <th className="px-4 py-2.5 font-medium">Action</th>
                  <th className="px-4 py-2.5 font-medium">Entity</th>
                  <th className="hidden px-4 py-2.5 font-medium md:table-cell">Details</th>
                </tr>
              </thead>
              <tbody>
                {activity.slice(0, 25).map((a) => (
                  <tr key={a.id} className="border-b border-base-border/40">
                    <td className="px-4 py-2 text-muted">{timeAgo(a.created_at)}</td>
                    <td className="px-4 py-2 text-secondary">{a.user}</td>
                    <td className="px-4 py-2"><span className="font-mono text-sky-400">{a.action}</span></td>
                    <td className="px-4 py-2 text-muted">{a.entity}</td>
                    <td className="hidden px-4 py-2 text-muted/70 md:table-cell">{JSON.stringify(a.details).slice(0, 80)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
