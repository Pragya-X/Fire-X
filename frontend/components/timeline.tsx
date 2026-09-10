"use client";

import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";

export interface TimelineDay {
  date: string;
  detected: boolean;
  count: number;
}

export function DetectionTimeline({ days }: { days: TimelineDay[] }) {
  if (!days.length) return <p className="text-xs text-muted">No temporal data available.</p>;
  return (
    <div className="flex flex-wrap items-end gap-1" role="img" aria-label="14-day detection timeline">
      {days.map((d) => (
        <div key={d.date} className="flex flex-col items-center gap-1" title={`${d.date}: ${d.count} detection(s)`}>
          <div className={cn("flex h-8 w-5 items-end justify-center rounded-sm border", d.detected ? "border-critical/50 bg-critical/15" : "border-base-border bg-base-raised/40")}>
            {d.detected && <Flame className="mb-0.5 h-3.5 w-3.5 text-critical" />}
          </div>
          <span className="text-[8px] text-muted">{d.date.slice(8)}</span>
        </div>
      ))}
    </div>
  );
}

export function HistoryTimeline({ history, className }: { history: { detection_time: string; brightness: number; frp: number }[]; className?: string }) {
  if (!history.length) return <p className="text-xs text-muted">First detection at this location.</p>;
  return (
    <ol className={cn("relative ml-3 space-y-3 border-l border-base-border pl-4", className)}>
      {[...history].reverse().map((h, i) => (
        <li key={i} className="relative">
          <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-sky-500/80" />
          <p className="text-[11px] text-secondary">{new Date(h.detection_time).toLocaleString("en-IN")}</p>
          <p className="text-[10px] text-muted">
            Brightness {h.brightness.toFixed(1)} K · FRP {h.frp.toFixed(1)} MW
          </p>
        </li>
      ))}
    </ol>
  );
}