"use client";

import { Layers, Satellite, Map as MapIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LayerId } from "@/components/map/map-view";

const LABELS: Record<LayerId, string> = {
  hotspots: "FIRMS hotspots",
  heatmap: "Risk heatmap",
  zones: "Industrial zones",
  refineries: "Refineries",
  factories: "Factories",
  power: "Power plants",
  mines: "Mines",
  settlements: "Settlements",
  forest: "Forest",
  agriculture: "Agriculture",
  roads: "Roads",
  railways: "Railways",
  pipelines: "Pipelines",
};

export function LayerControl({
  visible,
  onChange,
  basemap,
  onBasemap,
}: {
  visible: Record<LayerId, boolean>;
  onChange: (v: Record<LayerId, boolean>) => void;
  basemap: "dark" | "satellite";
  onBasemap: (b: "dark" | "satellite") => void;
}) {
  const ids = Object.keys(visible) as LayerId[];
  return (
    <div className="absolute left-3 top-3 z-10 w-48 rounded-lg border border-base-border bg-base-panel p-2.5 shadow-panel">
      <div className="mb-2 flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted">
          <Layers className="h-3.5 w-3.5" /> Layers
        </span>
        <div className="flex overflow-hidden rounded border border-base-border">
          <button
            onClick={() => onBasemap("dark")}
            aria-label="Dark basemap"
            className={cn("flex items-center gap-1 px-1.5 py-1 text-[10px]", basemap === "dark" ? "bg-sky-600/70 text-primary" : "text-muted hover:text-primary")}
          >
            <MapIcon className="h-3 w-3" /> Dark
          </button>
          <button
            onClick={() => onBasemap("satellite")}
            aria-label="Satellite basemap"
            className={cn("flex items-center gap-1 px-1.5 py-1 text-[10px]", basemap === "satellite" ? "bg-sky-600/70 text-primary" : "text-muted hover:text-primary")}
          >
            <Satellite className="h-3 w-3" /> Sat
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-0.5">
        {ids.map((id) => (
          <label key={id} className="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 text-[11px] text-secondary hover:bg-base-raised/50">
            <input
              type="checkbox"
              checked={visible[id]}
              onChange={() => onChange({ ...visible, [id]: !visible[id] })}
              className="h-3 w-3 accent-sky-500"
            />
            {LABELS[id]}
          </label>
        ))}
      </div>
    </div>
  );
}