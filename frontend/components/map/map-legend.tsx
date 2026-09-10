"use client";

import type { LayerId } from "@/components/map/map-view";

const RISK_ITEMS = [
  { color: "#ef4444", label: "CRITICAL (81-100)" },
  { color: "#f97316", label: "HIGH (61-80)" },
  { color: "#eab308", label: "ELEVATED (41-60)" },
  { color: "#3b82f6", label: "MODERATE (21-40)" },
  { color: "#22c55e", label: "LOW (0-20)" },
];

export function MapLegend({ visible }: { visible: Record<LayerId, boolean> }) {
  return (
    <div className="absolute bottom-8 right-3 z-10 hidden w-44 rounded-lg border border-base-border bg-base-panel p-2.5 shadow-panel md:block">
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted">Risk legend</p>
      <div className="flex flex-col gap-1">
        {RISK_ITEMS.map((r) => (
          <div key={r.label} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: r.color, boxShadow: `0 0 6px ${r.color}66` }} />
            <span className="text-[10px] text-muted">{r.label}</span>
          </div>
        ))}
      </div>
      {visible.heatmap && <p className="mt-2 border-t border-base-border pt-1.5 text-[9px] text-muted">Heatmap shows density-weighted risk.</p>}
    </div>
  );
}