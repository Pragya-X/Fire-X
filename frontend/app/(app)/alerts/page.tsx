"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Bell, CheckCircle2, ChevronRight, ShieldAlert, Siren } from "lucide-react";
import { acknowledgeAlert, escalateAlert, getAlerts, resolveAlert } from "@/lib/api";
import type { AlertItem } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, EmptyState, ErrorState, Select, Skeleton, useToast } from "@/components/ui/primitives";
import { RiskBadge } from "@/components/badges";
import { cn, timeAgo } from "@/lib/utils";

const STATUS_TONE: Record<string, "critical" | "high" | "moderate" | "info" | "low" | "muted" | "purple"> = {
  new: "critical",
  acknowledged: "high",
  investigating: "moderate",
  escalated: "purple",
  resolved: "low",
};

export default function AlertsPage() {
  const { push } = useToast();
  const [items, setItems] = useState<AlertItem[]>([]);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAlerts(statusFilter ? { status: statusFilter } : {});
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

  const act = async (id: number, fn: (id: number) => Promise<AlertItem>, label: string) => {
    setBusyId(id);
    try {
      const updated = await fn(id);
      setItems((prev) => prev.map((a) => (a.id === id ? updated : a)));
      push({ title: `Alert ${label}`, message: `${updated.code} → ${updated.status}`, tone: "success" });
    } catch (e) {
      push({ title: `Could not ${label}`, message: e instanceof Error ? e.message : "Action failed", tone: "error" });
    } finally {
      setBusyId(null);
    }
  };

  const counts = items.reduce<Record<string, number>>((acc, a) => {
    acc[a.status] = (acc[a.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-secondary tracking-tight">Alert Center</h1>
          <p className="text-xs text-muted/70 mt-0.5">{total} active alerts · thresholds: risk ≥ 80 or high-confidence industrial fires</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {["", "new", "acknowledged", "investigating", "escalated", "resolved"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                "rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition-colors",
                statusFilter === s ? "border-accent/60 bg-sky-600/20 text-secondary" : "border-base-border text-muted hover:text-secondary"
              )}
            >
              {s === "" ? "All" : s}
              {s && counts[s] ? ` (${counts[s]})` : ""}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {loading && <Skeleton className="h-40" />}

      {!loading && !error && items.length === 0 && <EmptyState title="No alerts" message="Alerts appear here when risk thresholds are crossed or demo scenario runs." />}

      <div className="space-y-2.5">
        {items.map((a) => (
          <Card key={a.id} className={cn("px-4 py-3", a.status === "new" && "border-critical/60")}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-bold text-sky-400">{a.code}</span>
                  {a.status === "new" ? <Siren className="h-3.5 w-3.5 text-critical" /> : <Bell className="h-3.5 w-3.5 text-muted/70" />}
                  <Badge tone={STATUS_TONE[a.status] ?? "muted"}>{a.status.toUpperCase()}</Badge>
                  <RiskBadge level={a.risk_score >= 81 ? "CRITICAL" : a.risk_score >= 61 ? "HIGH" : a.risk_score >= 41 ? "ELEVATED" : "MODERATE"} score={a.risk_score} />
                  <span className="text-[10px] text-muted/70">{timeAgo(a.created_at)}</span>
                </div>
                <h3 className="mt-1.5 text-sm font-semibold text-secondary">{a.title}</h3>
                <p className="mt-0.5 text-xs text-muted">{a.message}</p>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-[10px] text-muted/70">
                  <span>Location: {a.location}</span>
                  <span>Confidence: {Math.round(a.confidence * 100)}%</span>
                  {a.assigned_officer && <span>Officer: {a.assigned_officer}</span>}
                </div>
                <p className="mt-1.5 text-[11px] text-muted">
                  <AlertTriangle className="mr-1 inline h-3 w-3 text-moderate" />
                  {a.recommended_action}
                </p>
              </div>
              <div className="flex shrink-0 flex-col gap-1.5">
                {a.hotspot_id && (
                  <Link href={`/hotspots/${a.hotspot_id}`}>
                    <Button variant="ghost" size="sm" className="w-full justify-start"><ChevronRight className="h-3.5 w-3.5" /> View hotspot</Button>
                  </Link>
                )}
                {a.status === "new" && (
                  <Button size="sm" variant="outline" disabled={busyId === a.id} onClick={() => act(a.id, acknowledgeAlert, "acknowledged")}>
                    <CheckCircle2 className="h-3.5 w-3.5" /> Acknowledge
                  </Button>
                )}
                {["new", "acknowledged", "investigating"].includes(a.status) && a.status !== "escalated" && (
                  <Button size="sm" variant="outline" disabled={busyId === a.id} onClick={() => act(a.id, escalateAlert, "escalated")}>
                    <ShieldAlert className="h-3.5 w-3.5" /> Escalate
                  </Button>
                )}
                {a.status !== "resolved" && (
                  <Button size="sm" variant="success" disabled={busyId === a.id} onClick={() => act(a.id, resolveAlert, "resolved")}>
                    <CheckCircle2 className="h-3.5 w-3.5" /> Resolve
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}