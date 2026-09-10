"use client";

import { useCallback, useEffect, useState } from "react";
import { Brain, Cpu, FlaskConical, Loader2, Play, Sparkles } from "lucide-react";
import { classifyHotspot, getHotspots, getMlStatus } from "@/lib/api";
import type { Hotspot } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, Select, Skeleton, useToast } from "@/components/ui/primitives";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { ConfidenceGauge } from "@/components/gauges";
import { FeatureImportance } from "@/components/feature-importance";

const CLASS_COLORS: Record<string, string> = {
  "Industrial Fire": "#ef4444",
  "Persistent Industrial Heat Source": "#3b82f6",
  "Gas Flare": "#a855f7",
  Wildfire: "#f97316",
  "Agricultural Burning": "#eab308",
  "Other Thermal Anomaly": "#64748b",
};

export default function AiIntelligencePage() {
  const { push } = useToast();
  const [status, setStatus] = useState<{ online: boolean; mode: string; model_version: string; training_data_type: string; evaluation?: { test_accuracy?: number; model?: string; n_samples?: number } } | null>(null);

  const loadStatus = useCallback(() => {
    getMlStatus().then((s) => setStatus({ online: s.online, mode: s.mode, model_version: s.model_version, training_data_type: s.training_data_type, evaluation: s.evaluation as { test_accuracy?: number; model?: string; n_samples?: number } | undefined })).catch(() => setStatus(null));
  }, []);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [result, setResult] = useState<Awaited<ReturnType<typeof classifyHotspot>> | null>(null);
  const [running, setRunning] = useState(false);

  const load = useCallback(() => {
    loadStatus();
    getHotspots({ page_size: 100, sort: "risk_score", order: "desc" }).then((r) => setHotspots(r.items)).catch(() => undefined);
  }, [loadStatus]);

  useEffect(load, [load]);

  const run = async () => {
    if (!selectedId) return;
    setRunning(true);
    setResult(null);
    try {
      const res = await classifyHotspot(Number(selectedId));
      setResult(res);
      push({ title: "Classification complete", message: `${res.hotspot_code} → ${res.classification} (${Math.round(res.confidence * 100)}%)`, tone: "success" });
    } catch (e) {
      push({ title: "Classification failed", message: e instanceof Error ? e.message : "ML engine error", tone: "error" });
    } finally {
      setRunning(false);
    }
  };

  const modelNote = status
    ? `Version ${status.model_version} · Training data: ${status.training_data_type}. Probabilities are uncalibrated; rule scores are heuristic.`
    : "Model status unavailable";

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-700 tracking-tight">AI Intelligence Engine</h1>
        <p className="text-xs text-slate-400 mt-0.5">Classification pipeline · feature engineering · explainable ML predictions</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-1.5"><Cpu className="h-4 w-4 text-accent" /> Model status</CardTitle></CardHeader>
          <CardBody>
            {!status ? (
              <Skeleton className="h-20" />
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <Badge tone={status.online ? "low" : "moderate"}>{status.online ? "ONLINE" : "BASELINE"}</Badge>
                  <span className="text-xs text-slate-700">{status.mode}</span>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-slate-400">{modelNote}</p>
              </>
            )}
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-1.5"><Play className="h-4 w-4 text-accent" /> Classify a hotspot</CardTitle></CardHeader>
          <CardBody>
            <div className="flex flex-wrap items-center gap-2">
              <Select className="w-72" value={String(selectedId)} onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : "")} aria-label="Select hotspot">
                <option value="">Select hotspot (sorted by risk)...</option>
                {hotspots.map((h) => (
                  <option key={h.id} value={h.id}>{h.code} · {h.classification} · {h.risk_level}</option>
                ))}
              </Select>
              <Button onClick={run} disabled={!selectedId || running}>
                {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
                Run classification
              </Button>
            </div>
            <p className="mt-2 text-[10px] text-slate-400">Runs the full pipeline: temporal analysis → feature engineering → ML prediction → risk scoring → explanation.</p>
          </CardBody>
        </Card>
      </div>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5"><Brain className="h-4 w-4 text-accent" /> Result for {result.hotspot_code}</CardTitle>
            <RiskBadge level={result.risk_level} score={result.risk_score} />
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="space-y-4">
                <ClassificationBadge classification={result.classification} confidence={result.confidence} />
                <div className="w-56">
                  <ConfidenceGauge value={result.confidence} label="Classification confidence" />
                </div>
                <div>
                  <p className="mb-2 text-[10px] uppercase tracking-wider text-slate-400">Class probabilities</p>
                  <div className="space-y-1.5">
                    {Object.entries(result.probabilities).sort((a, b) => b[1] - a[1]).map(([c, p]) => (
                      <div key={c} className="flex items-center gap-2">
                        <span className="w-44 truncate text-[11px] text-slate-600">{c}</span>
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-base-panel">
                          <div className="h-full rounded-full" style={{ width: `${p * 100}%`, background: CLASS_COLORS[c] || "#64748b" }} />
                        </div>
                        <span className="w-10 text-right font-mono text-[10px] text-slate-400">{(p * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <p className="mb-2 text-[10px] uppercase tracking-wider text-slate-400">{result.feature_importance_type === "global_model_importance" ? "Global model importance" : "Heuristic context weights"}</p>
                <FeatureImportance importance={result.feature_importance} />
              </div>
              <div>
                <p className="mb-2 text-[10px] uppercase tracking-wider text-slate-400">Heuristic context explanation</p>
                <p className="flex items-center gap-1.5 text-[11px] text-slate-600"><Sparkles className="h-3 w-3 text-accent" /> {String((result.explanation as { reasoning?: string }).reasoning ?? "No reasoning available.")}</p>
                <div className="mt-3 space-y-1">
                  {Object.entries((result.explanation as { model_derived_factors?: Record<string, string> }).model_derived_factors ?? {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between rounded border border-base-border/40 bg-base-raised/30 px-2.5 py-1.5 text-[11px]">
                      <span className="text-slate-600">{k}</span>
                      <span className="font-semibold text-slate-700">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}