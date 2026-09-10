"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { TrendingUp, Flame, Mountain, Radar, Sprout, Thermometer, TriangleAlert } from "lucide-react";
import { getHotspotsGeojson, getHotspotStats, getSystemHealth } from "@/lib/api";
import type { GeoJson, HotspotStats, ScenarioResult } from "@/lib/types";
import { StatCard } from "@/components/stat-card";
import { Card, ErrorState, Skeleton } from "@/components/ui/primitives";
import { LiveFeed } from "@/components/dashboard/live-feed";
import { HotspotDetailPanel } from "@/components/dashboard/hotspot-detail-panel";
import { ScenarioPanel } from "@/components/dashboard/scenario-panel";

const MapView = dynamic(() => import("@/components/map/map-view").then((m) => m.MapView), {
  ssr: false,
  loading: () => <div className="flex h-full items-center justify-center bg-base-raised/40"><Skeleton className="h-40 w-40" /></div>,
});

export default function HomePage() {
  const [stats, setStats] = useState<HotspotStats | null>(null);
  const [geojson, setGeojson] = useState<GeoJson | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [focus, setFocus] = useState<{ lat: number; lon: number; zoom?: number; key?: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  const load = useCallback(async () => {
    setLoadError(null);
    getSystemHealth().then((health) => setDemoMode(health.demo_mode)).catch(() => setDemoMode(false));
    try {
      const [s, g] = await Promise.all([getHotspotStats(), getHotspotsGeojson()]);
      setStats(s);
      setGeojson(g);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Failed to load dashboard data");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, [load]);

  const handleScenarioStep = useCallback((phase: number, res: ScenarioResult) => {
    if (phase === 2 || phase === 5) {
      setFocus({ lat: res.hotspot.latitude, lon: res.hotspot.longitude, zoom: 11, key: `scenario-${phase}-${Date.now()}` });
      setSelected(res.hotspot.id);
    }
    if (phase === 5) setTimeout(load, 1500);
  }, [load]);

  const handleScenarioRestore = useCallback((res: ScenarioResult) => {
    setFocus({ lat: res.hotspot.latitude, lon: res.hotspot.longitude, zoom: 11, key: `restore-${Date.now()}` });
    setSelected(res.hotspot.id);
    load();
  }, [load]);

  const kpis = useMemo(
    () => [
      { label: "Active Hotspots", value: stats?.total ?? 0, change: stats?.week_change_pct, tone: "info" as const, icon: <TrendingUp className="h-5 w-5" strokeWidth={3} /> },
      { label: "Critical", value: stats?.critical ?? 0, change: undefined, tone: "critical" as const, icon: <TriangleAlert className="h-5 w-5 text-critical" fill="white" /> },
      { label: "Industrial Fires", value: stats?.industrial_fires ?? 0, change: undefined, tone: "high" as const, icon: <Flame className="h-5 w-5" fill="currentColor" /> },
      { label: "Wildfires", value: stats?.wildfires ?? 0, change: undefined, tone: "high" as const, icon: <Mountain className="h-5 w-5" fill="currentColor" /> },
      { label: "Agricultural Burns", value: stats?.agricultural_burns ?? 0, change: undefined, tone: "moderate" as const, icon: <Sprout className="h-5 w-5" fill="currentColor" /> },
      { label: "Persistent Heat", value: stats?.persistent_sources ?? 0, change: undefined, tone: "info" as const, icon: <Thermometer className="h-5 w-5 text-info" fill="white" /> },
    ],
    [stats]
  );

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <h1 className="text-lg font-bold text-secondary">Home</h1>
        <p className="text-xs text-muted">Latest stored hotspots powered by live NASA FIRMS integration.</p>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {kpis.map((k) => (
          <StatCard key={k.label} label={k.label} value={k.value} change={k.change} tone={k.tone} icon={k.icon} />
        ))}
      </div>

      {loadError && <ErrorState message={`Live provider unavailable - showing cached data: ${loadError}`} onRetry={load} />}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
        <div id="live-map" aria-label="Live Map" className="relative overflow-hidden rounded-lg border border-base-border bg-base-panel shadow-panel" style={{ height: "clamp(420px, 60vh, 800px)" }}>
          <MapView hotspots={geojson} selectedId={selected} onSelect={(id) => setSelected(id)} focus={focus} />
        </div>
        <div className="flex min-h-[300px] flex-col gap-4">
          {demoMode && <ScenarioPanel onStep={handleScenarioStep} onDone={load} onRestore={handleScenarioRestore} />}
          <div className="min-h-0 flex-1">
            <LiveFeed />
          </div>
        </div>
      </div>

      {selected && (
        <div className="fixed bottom-16 right-4 z-30 hidden lg:block" style={{ height: "min(70vh, 640px)" }}>
          <HotspotDetailPanel hotspotId={selected} onClose={() => setSelected(null)} />
        </div>
      )}
    </div>
  );
}
