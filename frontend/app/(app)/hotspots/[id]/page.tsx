"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Brain, Download, FileText, Info, MapPin, Thermometer } from "lucide-react";
import { downloadHotspotReport, getHotspot } from "@/lib/api";
import type { HotspotDetail } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, ErrorState, Skeleton, useToast } from "@/components/ui/primitives";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { ConfidenceGauge, RiskGauge } from "@/components/gauges";
import { FactorList, FeatureImportance } from "@/components/feature-importance";
import { DetectionTimeline, HistoryTimeline } from "@/components/timeline";
import { download, fmt, fmtDt } from "@/lib/utils";

export default function HotspotIntelligencePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { push } = useToast();
  const [data, setData] = useState<HotspotDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getHotspot(id)
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(load, [load]);

  const report = async () => {
    if (!data) return;
    try {
      const blob = await downloadHotspotReport(data.id);
      download(`${data.code}-incident-report.pdf`, blob);
      push({ title: "Incident report downloaded", message: `${data.code} PDF generated from live data.`, tone: "success" });
    } catch (e) {
      push({ title: "Report failed", message: e instanceof Error ? e.message : "Could not generate report", tone: "error" });
    }
  };

  const temporalDays = useMemo(() => {
    if (!data?.history) return [];
    const days = new Map<string, { date: string; detected: boolean; count: number }>();
    const end = data.acquisition_time ? new Date(data.acquisition_time) : new Date();
    for (let i = 13; i >= 0; i--) {
      const d = new Date(end.getTime() - i * 86400000);
      const key = d.toISOString().slice(0, 10);
      days.set(key, { date: key, detected: false, count: 0 });
    }
    for (const h of data.history) {
      const key = new Date(h.detection_time).toISOString().slice(0, 10);
      const day = days.get(key);
      if (day) { day.detected = true; day.count += 1; }
    }
    const acqKey = end.toISOString().slice(0, 10);
    const acq = days.get(acqKey);
    if (acq) { acq.detected = true; acq.count += 1; }
    return [...days.values()];
  }, [data]);

  const importance = useMemo(() => {
    const names = ["brightness", "frp", "n_detections", "persistence_score", "dist_industrial_km", "dist_forest_km", "dist_agriculture_km", "dist_settlement_km", "land_cover_code", "time_of_day", "historical_frequency", "satellite_score", "frp_normalized", "brightness_normalized"];
    const vec = data?.feature_vector ?? [];
    const imp: Record<string, number> = {};
    names.forEach((n, i) => { imp[n] = i < vec.length ? Math.abs(Number(vec[i])) : 0; });
    const total = Object.values(imp).reduce((a, b) => a + b, 0) || 1;
    Object.keys(imp).forEach((k) => (imp[k] = imp[k] / total));
    return imp;
  }, [data]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3"><Skeleton className="h-64" /><Skeleton className="h-64" /><Skeleton className="h-64" /></div>
      </div>
    );
  }
  if (error || !data) return <ErrorState message={error ?? "Hotspot not found"} onRetry={load} />;

  const f = data.features;
  const contextual = data.explanation?.contextual_factors ?? [];
  const reasoning = data.explanation?.reasoning ?? "";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-mono text-xl font-bold text-white">{data.code}</h1>
            <ClassificationBadge classification={data.classification} confidence={data.classification_confidence} />
            <RiskBadge level={data.risk_level} score={data.risk_score} />
            <Badge tone={data.source === "scenario" ? "purple" : "muted"}>{data.source.toUpperCase()}</Badge>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            <MapPin className="mr-1 inline h-3 w-3" />
            {data.latitude.toFixed(5)}, {data.longitude.toFixed(5)} · {data.state} / {data.district} · detected {fmtDt(data.acquisition_time)}
          </p>
        </div>
        <Button onClick={report}><FileText className="h-4 w-4" /> Incident report (PDF)</Button>
      </div>

      {/* Detection summary */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
        {[
          { l: "Satellite", v: data.satellite },
          { l: "Brightness", v: `${fmt(data.brightness)} K` },
          { l: "FRP", v: `${fmt(data.frp, 1)} MW` },
          { l: "Confidence", v: `${Math.round(data.confidence * 100)}%` },
          { l: "Persistence", v: `${Math.round(data.persistence_score)}/100` },
          { l: "Pattern", v: data.temporal_pattern },
          { l: "Land cover", v: data.land_cover },
          { l: "Status", v: data.status },
        ].map((x) => (
          <Card key={x.l} className="px-3 py-2.5">
            <p className="text-[9px] uppercase tracking-wider text-slate-400">{x.l}</p>
            <p className="mt-0.5 truncate text-xs font-semibold text-slate-200">{x.v}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Risk */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-1.5"><Thermometer className="h-4 w-4 text-accent" /> Risk assessment</CardTitle></CardHeader>
          <CardBody className="flex flex-col items-center">
            <RiskGauge score={data.risk_score} level={data.risk_level} size={170} />
            <p className="mt-3 text-center text-xs text-slate-400">
              {data.risk_score >= 81 ? "Immediate field verification recommended." : data.risk_score >= 61 ? "Priority inspection recommended." : data.risk_score >= 41 ? "Enhanced monitoring recommended." : data.risk_score >= 21 ? "Continue monitoring." : "No immediate action required."}
            </p>
            <div className="mt-4 w-full">
              <ConfidenceGauge value={data.classification_confidence} label="Classification confidence" />
            </div>
          </CardBody>
        </Card>

        {/* Spatial context */}
        <Card>
          <CardHeader><CardTitle>Spatial context</CardTitle></CardHeader>
          <CardBody>
            {f ? (
              <div className="grid grid-cols-1 gap-1.5">
                {[
                  { l: "Nearest refinery", v: f.nearest_refinery_distance },
                  { l: "Nearest factory", v: f.nearest_factory_distance },
                  { l: "Nearest power plant", v: f.nearest_powerplant_distance },
                  { l: "Nearest mine", v: f.nearest_mine_distance },
                  { l: "Nearest forest", v: f.nearest_forest_distance },
                  { l: "Nearest agricultural area", v: f.nearest_agriculture_distance },
                  { l: "Nearest settlement", v: f.nearest_settlement_distance },
                  { l: "Nearest road", v: f.nearest_road_distance },
                  { l: "Nearest railway", v: f.nearest_railway_distance },
                  { l: "Nearest pipeline", v: f.nearest_pipeline_distance },
                ].map((x) => (
                  <div key={x.l} className="flex items-center justify-between rounded border border-base-border/40 bg-base-raised/30 px-2.5 py-1.5">
                    <span className="text-[11px] text-slate-400">{x.l}</span>
                    <span className="font-mono text-[11px] font-semibold text-slate-200">{x.v >= 0 ? `${fmt(x.v)} km` : "n/a"}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">Spatial features not computed.</p>
            )}
          </CardBody>
        </Card>

        {/* Temporal */}
        <Card>
          <CardHeader><CardTitle>Temporal analysis</CardTitle></CardHeader>
          <CardBody>
            <div className="mb-3 flex items-center gap-2">
              <Badge tone={data.temporal_pattern === "persistent" ? "info" : data.temporal_pattern === "sudden" ? "critical" : data.temporal_pattern === "recurring" ? "moderate" : "muted"}>
                {data.temporal_pattern.toUpperCase()}
              </Badge>
              <span className="text-[11px] text-slate-400">{data.history.length} prior detections</span>
            </div>
            <p className="mb-2 text-[10px] uppercase tracking-wider text-slate-400">14-day detection timeline</p>
            <DetectionTimeline days={temporalDays} />
            <div className="mt-4">
              <p className="mb-2 text-[10px] uppercase tracking-wider text-slate-400">Detection history</p>
              <HistoryTimeline history={data.history} />
            </div>
          </CardBody>
        </Card>
      </div>

      {/* AI explanation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-1.5"><Brain className="h-4 w-4 text-accent" /> AI explanation</CardTitle>
          <Badge tone="info">Model-derived + rule-based</Badge>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div>
              <p className="mb-2 text-xs font-semibold text-slate-300">Model-derived factors</p>
              <FactorList factors={data.explanation?.model_derived_factors ?? {}} />
              {data.explanation?.probability_gap_pct !== undefined && (
                <p className="mt-2 flex items-center gap-1.5 text-[10px] text-slate-400">
                  <Info className="h-3 w-3" />
                  Probability gap vs runner-up: {data.explanation.probability_gap_pct}% ({data.explanation.runner_up ?? "none"})
                </p>
              )}
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold text-slate-300">Feature importance</p>
              <FeatureImportance importance={importance} />
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold text-slate-300">Contextual factors (rule-based)</p>
              <ul className="space-y-1">
                {contextual.length === 0 && <li className="text-xs text-slate-400">No contextual factors recorded.</li>}
                {contextual.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-[11px] text-slate-400">
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-accent" />{c}
                  </li>
                ))}
              </ul>
              {reasoning && (
                <div className="mt-3 rounded-md border border-accent/20 bg-sky-600/5 p-3">
                  <p className="text-[11px] leading-relaxed text-slate-300">{reasoning}</p>
                </div>
              )}
              <p className="mt-3 text-[9px] text-slate-600">
                Model-derived factors come from the trained classifier; contextual factors are rule-based heuristics and are not model explanations.
              </p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Download */}
      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={report}><Download className="h-3.5 w-3.5" /> Download report</Button>
      </div>
    </div>
  );
}