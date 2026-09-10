"use client";

import Link from "next/link";
import { FileText, Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { getHotspot, downloadHotspotReport } from "@/lib/api";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { ConfidenceGauge, RiskGauge } from "@/components/gauges";
import { Button, Skeleton, useToast } from "@/components/ui/primitives";
import { download, fmt } from "@/lib/utils";
import type { HotspotDetail } from "@/lib/types";

export function HotspotDetailPanel({ hotspotId, onClose }: { hotspotId: number | null; onClose: () => void }) {
  const [data, setData] = useState<HotspotDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { push } = useToast();

  useEffect(() => {
    if (!hotspotId) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    getHotspot(hotspotId)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [hotspotId]);

  const report = async () => {
    if (!data) return;
    try {
      const blob = await downloadHotspotReport(data.id);
      download(`${data.code}-incident-report.pdf`, blob);
      push({ title: "Report generated", message: `${data.code} incident report downloaded.`, tone: "success" });
    } catch (e) {
      push({ title: "Report failed", message: e instanceof Error ? e.message : "Could not generate report", tone: "error" });
    }
  };

  if (!hotspotId) return null;

  const f = data?.features;

  return (
    <aside className="flex w-full flex-col overflow-hidden rounded-lg border border-base-border bg-base-panel shadow-panel lg:w-[360px] lg:max-h-full">
      <div className="flex items-center justify-between border-b border-base-border/70 px-4 py-3">
        <div>
          <p className="font-mono text-sm font-bold text-slate-900">{data?.code ?? "Hotspot"}</p>
          <p className="text-[10px] text-slate-500">{data ? `${data.state} / ${data.district}` : "Loading..."}</p>
        </div>
        <button onClick={onClose} className="rounded p-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900" aria-label="Close panel">
          <X className="h-4 w-4" />
        </button>
      </div>

      {loading && (
        <div className="space-y-3 p-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-20" />
          <Skeleton className="h-40" />
        </div>
      )}
      {error && <p className="p-4 text-xs text-critical">{error}</p>}

      {data && (
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          <div className="flex items-center justify-between gap-2">
            <ClassificationBadge classification={data.classification} confidence={data.classification_confidence} />
            <RiskBadge level={data.risk_level} score={data.risk_score} />
          </div>

          <div className="flex items-center justify-center rounded-lg border border-base-border/60 bg-base-raised/40 py-3">
            <RiskGauge score={data.risk_score} level={data.risk_level} size={130} />
          </div>

          <div>
            <p className="mb-1 text-[10px] uppercase tracking-wider text-slate-500">Thermal signature</p>
            <div className="grid grid-cols-3 gap-2 text-center">
              {[
                { l: "Brightness", v: `${fmt(data.brightness)} K` },
                { l: "FRP", v: `${fmt(data.frp, 1)} MW` },
                { l: "Confidence", v: `${Math.round(data.confidence * 100)}%` },
              ].map((x) => (
                <div key={x.l} className="rounded-md border border-base-border/50 bg-base-raised/40 px-2 py-2">
                  <p className="font-mono text-xs font-semibold text-slate-900">{x.v}</p>
                  <p className="text-[9px] text-slate-500">{x.l}</p>
                </div>
              ))}
            </div>
          </div>

          {f && (
            <div>
              <p className="mb-1.5 text-[10px] uppercase tracking-wider text-slate-500">Spatial context</p>
              <div className="space-y-1">
                {[
                  { l: "Nearest refinery", v: f.nearest_refinery_distance },
                  { l: "Nearest factory", v: f.nearest_factory_distance },
                  { l: "Nearest power plant", v: f.nearest_powerplant_distance },
                  { l: "Nearest settlement", v: f.nearest_settlement_distance },
                  { l: "Nearest forest", v: f.nearest_forest_distance },
                  { l: "Nearest pipeline", v: f.nearest_pipeline_distance },
                ].map((x) => (
                  <div key={x.l} className="flex items-center justify-between rounded border border-base-border/40 bg-base-raised/30 px-2.5 py-1.5">
                    <span className="text-[11px] text-slate-600">{x.l}</span>
                    <span className="font-mono text-[11px] font-semibold text-slate-900">{x.v >= 0 ? `${fmt(x.v)} km` : "n/a"}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2">
            <Button size="sm" onClick={report}>
              <FileText className="h-3.5 w-3.5" /> Generate incident report (PDF)
            </Button>
            <Link href={`/hotspots/${data.id}`} className="w-full">
              <Button variant="outline" size="sm" className="w-full">
                Open full intelligence view
              </Button>
            </Link>
          </div>
        </div>
      )}
    </aside>
  );
}

export { Loader2 };