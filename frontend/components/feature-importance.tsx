"use client";

import { cn } from "@/lib/utils";

const LABELS: Record<string, string> = {
  brightness: "Thermal intensity",
  frp: "FRP",
  n_detections: "Detection count",
  persistence_score: "Persistence",
  dist_industrial_km: "Industrial proximity",
  dist_forest_km: "Forest proximity",
  dist_agriculture_km: "Agriculture proximity",
  dist_settlement_km: "Settlement proximity",
  land_cover_code: "Land cover",
  time_of_day: "Time of day",
  historical_frequency: "Historical frequency",
  satellite_score: "Satellite score",
  frp_normalized: "FRP (normalized)",
  brightness_normalized: "Brightness (normalized)",
};

export function FeatureImportance({
  importance,
  limit = 8,
  className,
}: {
  importance: Record<string, number>;
  limit?: number;
  className?: string;
}) {
  const entries = Object.entries(importance)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
  const max = Math.max(...entries.map(([, v]) => v), 0.001);

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-center gap-2">
          <span className="w-36 shrink-0 text-[11px] text-muted">{LABELS[key] || key}</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800/80">
            <div
              className="h-full rounded-full bg-sky-500/80"
              style={{ width: `${(value / max) * 100}%`, boxShadow: "0 0 6px rgba(56,189,248,0.4)" }}
            />
          </div>
          <span className="w-12 shrink-0 text-right font-mono text-[10px] text-muted">{value.toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

export function FactorList({ factors }: { factors: Record<string, string> }) {
  return (
    <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
      {Object.entries(factors).map(([k, v]) => {
        const tone =
          v === "VERY HIGH" || v === "HIGH" ? "text-critical" : v === "MODERATE" ? "text-moderate" : v === "LOW" ? "text-low" : "text-secondary";
        return (
          <div key={k} className="flex items-center justify-between rounded border border-base-border/60 bg-base-raised/40 px-2.5 py-1.5">
            <span className="text-[11px] text-muted">{k}</span>
            <span className={cn("text-[11px] font-semibold", tone)}>{v}</span>
          </div>
        );
      })}
    </div>
  );
}