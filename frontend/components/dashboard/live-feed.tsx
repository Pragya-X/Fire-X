"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Bell, Flame, Radar, Satellite, Thermometer } from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/primitives";
import { useSSE } from "@/hooks/useSSE";
import { timeAgo } from "@/lib/utils";

const TYPE_META: Record<string, { label: string; tone: string; icon: React.ReactNode }> = {
  ingest: { label: "New hotspot", tone: "text-high", icon: <Flame className="h-3.5 w-3.5" /> },
  scenario: { label: "Demo scenario", tone: "text-purple-400", icon: <Activity className="h-3.5 w-3.5" /> },
  notification: { label: "Alert generated", tone: "text-critical", icon: <Bell className="h-3.5 w-3.5" /> },
  alert_update: { label: "Alert update", tone: "text-moderate", icon: <AlertTriangle className="h-3.5 w-3.5" /> },
  satellite_validation: { label: "Satellite validation", tone: "text-info", icon: <Satellite className="h-3.5 w-3.5" /> },
};

interface FeedItem {
  id: number;
  type: string;
  label: string;
  detail: string;
  at: Date;
}

export function LiveFeed() {
  const { latest } = useSSE(30);
  const [items, setItems] = useState<FeedItem[]>([]);

  useEffect(() => {
    if (!latest) return;
    const meta = TYPE_META[latest.type] || { label: "System event", tone: "text-muted", icon: <Radar className="h-3.5 w-3.5" /> };
    const data = (latest.data ?? {}) as Record<string, unknown>;
    let detail = JSON.stringify(data).slice(0, 90);
    if (latest.type === "notification" && typeof data.title === "string") detail = data.title;
    if (latest.type === "ingest" && data.created) detail = `${data.created} new detection(s) ingested`;
    if (latest.type === "scenario" && data.phase) detail = `Phase ${data.phase}: ${data.classification ?? "updating"}`;
    if (latest.type === "satellite_validation") detail = `Validation ${data.status} for ${data.hotspot}`;
    setItems((prev) => [{ id: Date.now(), type: latest.type, label: meta.label, detail: String(detail), at: new Date() }, ...prev].slice(0, 30));
  }, [latest]);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="relative inline-flex h-2 w-2 rounded-full bg-low" />
          </span>
          Live Activity Feed
        </CardTitle>
        <span className="text-[10px] uppercase tracking-wider text-muted">SSE stream</span>
      </CardHeader>
      <CardBody className="flex-1 overflow-y-auto p-3">
        {items.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-muted">
            <Activity className="h-6 w-6" />
            <p className="text-xs">Waiting for events...</p>
            <p className="text-[10px]">Run the demo scenario or sync FIRMS data to see live activity.</p>
          </div>
        )}
        <ul className="space-y-2">
          {items.map((it) => {
            const meta = TYPE_META[it.type] || { label: "System event", tone: "text-muted", icon: <Radar className="h-3.5 w-3.5" /> };
            return (
              <li key={it.id} className="animate-fadeIn rounded-md border border-base-border/50 bg-base-raised/40 px-2.5 py-2">
                <div className="flex items-center gap-2">
                  <span className={meta.tone}>{meta.icon}</span>
                  <span className="text-[11px] font-semibold text-primary">{it.label}</span>
                  <span className="ml-auto text-[9px] text-muted">{timeAgo(it.at.toISOString())}</span>
                </div>
                <p className="mt-0.5 line-clamp-2 pl-5 text-[10px] text-muted">{it.detail}</p>
              </li>
            );
          })}
        </ul>
      </CardBody>
    </Card>
  );
}

export { Thermometer };