"use client";

import { useCallback, useEffect, useState } from "react";
import { Cloud, Loader2, ScanSearch, Sprout, TreePine, Waves } from "lucide-react";
import { getHotspots, getValidations, validateSatellite } from "@/lib/api";
import type { Hotspot, SatelliteValidation } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, EmptyState, ErrorState, Select, Skeleton, useToast } from "@/components/ui/primitives";
import { SatelliteComparison } from "@/components/satellite-comparison";
import { RiskBadge } from "@/components/badges";
import { fmt } from "@/lib/utils";

const STATUS_TONE: Record<string, "low" | "info" | "moderate" | "muted"> = {
  CONFIRMED: "low",
  LIKELY: "info",
  UNCERTAIN: "moderate",
  "NOT VALIDATED": "muted",
};

export default function SatelliteValidationPage() {
  const { push } = useToast();
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [validations, setValidations] = useState<SatelliteValidation[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [current, setCurrent] = useState<SatelliteValidation | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, v] = await Promise.all([getHotspots({ page_size: 60, sort: "risk_score", order: "desc" }), getValidations()]);
      setHotspots(h.items);
      setValidations(v.items as SatelliteValidation[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load satellite data");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const select = (id: number) => {
    setSelectedId(id);
    const found = validations.find((v) => v.hotspot_id === id) ?? null;
    setCurrent(found);
  };

  const runValidation = async () => {
    if (!selectedId) return;
    setValidating(true);
    try {
      const res = await validateSatellite(Number(selectedId));
      setCurrent({ ...current, ...res, hotspot_id: Number(selectedId) } as SatelliteValidation);
      push({ title: "Validation complete", message: `Status: ${res.status} (${res.provider.toUpperCase()} mode)`, tone: res.status === "CONFIRMED" ? "success" : "info" });
      load();
    } catch (e) {
      push({ title: "Validation failed", message: e instanceof Error ? e.message : "Provider error", tone: "error" });
    } finally {
      setValidating(false);
    }
  };

  const hotspot = hotspots.find((h) => h.id === Number(selectedId));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-secondary tracking-tight">Satellite Validation</h1>
          <p className="text-xs text-muted/70 mt-0.5">Remote sensing analysis · before/after comparison · NDVI, burn area, fire extent</p>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Select hotspot</CardTitle></CardHeader>
        <CardBody>
          <div className="flex flex-wrap items-center gap-2">
            <Select className="w-80" value={String(selectedId)} onChange={(e) => select(Number(e.target.value))} aria-label="Select hotspot for validation">
              <option value="">Choose hotspot (by risk)...</option>
              {hotspots.map((h) => (
                <option key={h.id} value={h.id}>{h.code} · {h.classification} · risk {Math.round(h.risk_score)}</option>
              ))}
            </Select>
            <Button onClick={runValidation} disabled={!selectedId || validating}>
              {validating ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanSearch className="h-4 w-4" />}
              Run satellite validation
            </Button>
            {hotspot && <RiskBadge level={hotspot.risk_level} score={hotspot.risk_score} />}
          </div>
        </CardBody>
      </Card>

      {loading && <Skeleton className="h-80" />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && selectedId === "" && <EmptyState title="No hotspot selected" message="Pick a hotspot above to render the before/after comparison." />}

      {selectedId !== "" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Before / after comparison</CardTitle></CardHeader>
            <CardBody>
              <SatelliteComparison validation={current} />
              <p className="mt-3 text-[10px] leading-relaxed text-muted/70">
                Scene rendered from validation parameters (NDVI, burn area, fire extent, smoke). Live Sentinel-2 / Landsat imagery is used automatically when SATELLITE_API_KEY is configured.
              </p>
            </CardBody>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Validation status</CardTitle></CardHeader>
              <CardBody>
                {current ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge tone={STATUS_TONE[current.status] ?? "muted"}>{current.status}</Badge>
                      <span className="text-[10px] text-muted/70">provider: {current.provider.toUpperCase()}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { l: "Smoke indication", v: current.smoke_indication === null ? "Unavailable" : current.smoke_indication ? "DETECTED" : "None", icon: <Cloud className="h-3.5 w-3.5" />, tone: current.smoke_indication ? "text-critical" : "text-low" },
                        { l: "Burn area", v: current.burn_area_ha === null ? "Unavailable" : `${fmt(current.burn_area_ha)} ha`, icon: <TreePine className="h-3.5 w-3.5" />, tone: "text-secondary" },
                        { l: "Fire extent", v: current.fire_extent_km2 === null ? "Unavailable" : `${fmt(current.fire_extent_km2, 2)} km²`, icon: <Waves className="h-3.5 w-3.5" />, tone: "text-secondary" },
                        { l: "Vegetation delta (NDVI)", v: `${current.ndvi_before?.toFixed(2) ?? "Unavailable"} → ${current.ndvi_after?.toFixed(2) ?? "Unavailable"}`, icon: <Sprout className="h-3.5 w-3.5" />, tone: current.ndvi_after !== null && current.ndvi_before !== null && current.ndvi_after < current.ndvi_before ? "text-moderate" : "text-low" },
                      ].map((x) => (
                        <div key={x.l} className="rounded-md border border-base-border/50 bg-base-raised/40 px-3 py-2.5">
                          <p className="flex items-center gap-1.5 text-[9px] uppercase tracking-wider text-muted/70">{x.icon}{x.l}</p>
                          <p className={`mt-1 text-sm font-bold ${x.tone}`}>{x.v}</p>
                        </div>
                      ))}
                    </div>
                    {current.notes && <p className="rounded border border-base-border/40 bg-base-raised/30 px-3 py-2 text-[11px] text-muted">{current.notes}</p>}
                  </div>
                ) : (
                  <p className="py-4 text-center text-xs text-muted/70">No validation record yet for this hotspot. Run validation to generate one.</p>
                )}
              </CardBody>
            </Card>

            {hotspot && (
              <Card>
                <CardHeader><CardTitle>Hotspot context</CardTitle></CardHeader>
                <CardBody className="text-xs text-muted">
                  <p><span className="text-muted/70">Classification:</span> <span className="text-secondary">{hotspot.classification}</span></p>
                  <p className="mt-1"><span className="text-muted/70">Brightness:</span> <span className="text-secondary">{fmt(hotspot.brightness)} K</span></p>
                  <p className="mt-1"><span className="text-muted/70">FRP:</span> <span className="text-secondary">{fmt(hotspot.frp, 1)} MW</span></p>
                  <p className="mt-1"><span className="text-muted/70">Location:</span> <span className="text-secondary">{hotspot.latitude.toFixed(4)}, {hotspot.longitude.toFixed(4)}</span></p>
                </CardBody>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}