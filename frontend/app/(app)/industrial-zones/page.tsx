"use client";

import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Building2, Download, Factory, Flame, Gem, Landmark, Loader2, MapPin, Power, Users } from "lucide-react";
import { downloadZoneReport, getZone, getZonesGeojson, getIndustrialZones } from "@/lib/api";
import type { GeoJson, IndustrialZone, ZoneIntelligence } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, Dialog, ErrorState, Select, Skeleton, useToast } from "@/components/ui/primitives";
import { RiskBadge } from "@/components/badges";
import { download, fmt } from "@/lib/utils";

const MapView = dynamic(() => import("@/components/map/map-view").then((m) => m.MapView), { ssr: false, loading: () => <Skeleton className="h-64" /> });

const TYPE_ICON: Record<string, React.ReactNode> = {
  Refinery: <Landmark className="h-4 w-4" />,
  Factory: <Factory className="h-4 w-4" />,
  "Power Plant": <Power className="h-4 w-4" />,
  Mine: <Gem className="h-4 w-4" />,
  "Industrial Park": <Building2 className="h-4 w-4" />,
};

export default function IndustrialZonesPage() {
  const params = useSearchParams();
  const { push } = useToast();
  const [zones, setZones] = useState<IndustrialZone[]>([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [geojson, setGeojson] = useState<GeoJson | null>(null);
  const [focus, setFocus] = useState<{ lat: number; lon: number; zoom?: number; key?: string } | null>(null);
  const [detail, setDetail] = useState<ZoneIntelligence | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    getIndustrialZones().then((r) => setZones(r.items)).catch((e: Error) => setError(e.message));
    getZonesGeojson().then(setGeojson).catch(() => setGeojson(null));
  }, []);
  useEffect(load, [load]);

  // Deep link ?zone=ID
  useEffect(() => {
    const zid = params.get("zone");
    if (zid) openDetail(Number(zid));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const openDetail = (id: number) => {
    setDetailId(id);
    setLoadingDetail(true);
    setDetail(null);
    getZone(id)
      .then((z) => {
        setDetail(z);
        setFocus({ lat: z.zone.latitude, lon: z.zone.longitude, zoom: 10, key: `zone-${id}-${Date.now()}` });
      })
      .catch(() => push({ title: "Zone load failed", message: "Could not load zone intelligence.", tone: "error" }))
      .finally(() => setLoadingDetail(false));
  };

  const zoneReport = async (z: IndustrialZone) => {
    try {
      const blob = await downloadZoneReport(z.id);
      download(`${z.code}-zone-report.pdf`, blob);
      push({ title: "Zone report downloaded", message: `${z.name} PDF generated.`, tone: "success" });
    } catch (e) {
      push({ title: "Report failed", message: e instanceof Error ? e.message : "Could not generate report", tone: "error" });
    }
  };

  const filtered = typeFilter ? zones.filter((z) => z.zone_type === typeFilter) : zones;
  const types = Array.from(new Set(zones.map((z) => z.zone_type)));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-700 tracking-tight">Industrial Zone Monitoring</h1>
          <p className="text-xs text-slate-400">{zones.length} zones · persistent heat sources, fire risk, population exposure</p>
        </div>
        <Select className="w-52" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} aria-label="Filter zone type">
          <option value="">All zone types</option>
          {types.map((t) => <option key={t} value={t}>{t}</option>)}
        </Select>
      </div>

      <Card className="relative h-80 overflow-hidden">
        <MapView hotspots={null} focus={focus} className="h-full w-full" />
        <div className="pointer-events-none absolute left-1/2 top-3 z-10 -translate-x-1/2 rounded border border-base-border bg-base-panel px-3 py-1 text-[10px] uppercase tracking-widest text-slate-600">
          {detail ? detail.zone.name : "Click a zone card to zoom"}
        </div>
      </Card>

      {error && <ErrorState message={error} onRetry={load} />}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((z) => {
          const critical = z.risk_level === "CRITICAL";
          return (
            <Card key={z.id} className={critical ? "border-critical/60" : "cursor-pointer transition-colors hover:border-accent/50"} >
              <button className="block w-full text-left" onClick={() => openDetail(z.id)}>
                <CardBody>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`rounded-md border p-2 ${critical ? "border-critical/50 bg-critical/10 text-critical" : "border-base-border bg-base-raised text-accent"}`}>
                        {TYPE_ICON[z.zone_type] ?? <Building2 className="h-4 w-4" />}
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-slate-700">{z.name}</p>
                        <p className="text-[10px] text-slate-400">{z.zone_type} · {z.district}, {z.state}</p>
                      </div>
                    </div>
                    <RiskBadge level={z.risk_level} />
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded border border-base-border/40 bg-base-raised/30 px-1 py-1.5">
                      <p className="font-mono text-sm font-bold text-slate-700">{z.risk_level === "CRITICAL" ? "!" : "—"}</p>
                      <p className="text-[9px] text-slate-400">Current risk</p>
                    </div>
                    <div className="rounded border border-base-border/40 bg-base-raised/30 px-1 py-1.5">
                      <p className="font-mono text-sm font-bold text-slate-700">{z.monitoring_level}</p>
                      <p className="text-[9px] text-slate-400">Monitoring</p>
                    </div>
                    <div className="rounded border border-base-border/40 bg-base-raised/30 px-1 py-1.5">
                      <p className="font-mono text-sm font-bold text-slate-700">{(z.population_exposure / 1000).toFixed(0)}k</p>
                      <p className="text-[9px] text-slate-400">Population</p>
                    </div>
                  </div>
                </CardBody>
              </button>
            </Card>
          );
        })}
      </div>

      {/* Zone intelligence dialog */}
      <Dialog open={detailId !== null} onClose={() => setDetailId(null)} title={detail?.zone.name ?? "Zone intelligence"} wide>
        {loadingDetail && <Skeleton className="h-64" />}
        {detail && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <RiskBadge level={detail.zone.risk_level} />
              <Badge tone="info">{detail.zone.monitoring_level} MONITORING</Badge>
              <span className="text-xs text-slate-600">
                <MapPin className="mr-1 inline h-3 w-3" />{detail.zone.latitude.toFixed(4)}, {detail.zone.longitude.toFixed(4)} · {detail.zone.district}, {detail.zone.state}
              </span>
              <Button variant="outline" size="sm" className="ml-auto" onClick={() => zoneReport(detail.zone)}>
                <Download className="h-3.5 w-3.5" /> Zone report (PDF)
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                { l: "Hotspots within 1 km", v: detail.hotspots_1km, tone: detail.hotspots_1km > 0 ? "text-critical" : "text-slate-700" },
                { l: "Hotspots within 5 km", v: detail.hotspots_5km, tone: detail.hotspots_5km > 3 ? "text-high" : "text-slate-700" },
                { l: "Historical detections", v: detail.historical_activity, tone: "text-slate-700" },
                { l: "Active alerts", v: detail.alerts, tone: detail.alerts > 0 ? "text-moderate" : "text-slate-700" },
              ].map((x) => (
                <div key={x.l} className="rounded-md border border-base-border/50 bg-base-raised/40 px-3 py-2.5 text-center">
                  <p className={`font-mono text-xl font-bold ${x.tone}`}>{x.v}</p>
                  <p className="text-[9px] uppercase tracking-wider text-slate-400">{x.l}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-md border border-base-border/50 p-3">
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-700"><Users className="h-3.5 w-3.5 text-accent" /> Population exposure</p>
                <p className="text-lg font-bold text-slate-100">{detail.population_exposure.toLocaleString()}</p>
                <p className="text-[10px] text-slate-400">Estimated residents within 12 km of zone centre</p>
              </div>
              <div className="rounded-md border border-base-border/50 p-3">
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-700"><Flame className="h-3.5 w-3.5 text-accent" /> Recommended monitoring</p>
                <p className="text-lg font-bold text-slate-100">{detail.recommended_monitoring}</p>
                <p className="text-[10px] text-slate-400">Road access: {detail.road_access}</p>
              </div>
            </div>

            {detail.hotspots_1km_list.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-slate-700">Hotspots within 1 km (by risk)</p>
                <div className="max-h-52 space-y-1.5 overflow-y-auto">
                  {detail.hotspots_1km_list.map((h) => (
                    <div key={h.id} className="flex items-center justify-between rounded border border-base-border/40 bg-base-raised/30 px-2.5 py-1.5 text-[11px]">
                      <span className="font-mono font-semibold text-sky-400">{h.code}</span>
                      <span className="text-slate-600">{h.classification}</span>
                      <RiskBadge level={h.risk_level} score={h.risk_score} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Dialog>
    </div>
  );
}