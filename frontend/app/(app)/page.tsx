"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { TrendingUp, Flame, Mountain, Radar, Sprout, Thermometer, TriangleAlert, RefreshCw, Satellite } from "lucide-react";
import { getHotspotsGeojson, getHotspotStats, getSystemHealth, ingestFirms } from "@/lib/api";
import type { GeoJson, HotspotStats, ScenarioResult } from "@/lib/types";
import { useAuth } from "@/lib/auth";
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
  const { user } = useAuth();
  const [stats, setStats] = useState<HotspotStats | null>(null);
  const [geojson, setGeojson] = useState<GeoJson | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [focus, setFocus] = useState<{ lat: number; lon: number; zoom?: number; key?: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastSynced, setLastSynced] = useState<Date | null>(null);

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

  const sync = useCallback(() => {
    setSyncing(true);
    ingestFirms()
      .catch((e) => console.error("Sync failed:", e))
      .finally(() => {
        setLastSynced(new Date());
        setSyncing(false);
        load();
      });
  }, [load]);

  // Data freshness is handled by a server-side 2-minute scheduler; the
  // dashboard only refreshes its view and offers a manual sync button.
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

  const greeting = useMemo(() => {
    const h = new Date().getHours();
    if (h < 5) return "Good night";
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  }, []);

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Greeting hero — solid gradient banner with live stats inside */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-sky-600 via-sky-600 to-cyan-600 px-6 py-5 text-white shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-4">
          <div className="min-w-0">
            <p className="mb-1 inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-sky-50">
              <Satellite className="h-3 w-3" /> Live Fire Intelligence Network
            </p>
            <h1 className="text-xl font-bold leading-tight sm:text-2xl">
              {greeting}, {user?.name?.split(" ")[0] ?? "Operator"}
            </h1>
            <p className="mt-1 max-w-xl text-[13px] leading-relaxed text-sky-100">
              {stats
                ? `Tracking ${stats.total} active hotspots nationally with ${stats.critical} critical.${lastSynced ? ` Last synced ${lastSynced.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}.` : ""}`
                : "Connecting to the fire intelligence feed…"}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <a
                href="#live-map"
                className="flex items-center gap-1.5 rounded-lg bg-white px-3.5 py-2 text-[12px] font-semibold text-sky-700 shadow-sm transition-colors hover:bg-sky-50"
              >
                <Radar className="h-3.5 w-3.5" /> View live map
              </a>
              <button
                onClick={sync}
                disabled={syncing}
                className="flex items-center gap-1.5 rounded-lg border border-white/40 bg-white/10 px-3.5 py-2 text-[12px] font-semibold text-white transition-colors hover:bg-white/20 disabled:opacity-60"
              >
                {syncing ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Satellite className="h-3.5 w-3.5" />}
                {syncing ? "Syncing FIRMS…" : "Sync FIRMS now"}
              </button>
            </div>
          </div>

          {/* Mini stats inside the banner */}
          <div className="flex shrink-0 items-center gap-6">
            {[
              { label: "Active Hotspots", value: stats?.total ?? "—", sub: "Monitored nationally" },
              { label: "Critical", value: stats?.critical ?? "—", sub: "Immediate attention" },
              { label: "Industrial Fires", value: stats?.industrial_fires ?? "—", sub: "Near facilities" },
            ].map((s) => (
              <div key={s.label} className="hidden text-right sm:block">
                <p className="text-[10px] font-medium uppercase tracking-wider text-sky-100">{s.label}</p>
                <p className="font-mono text-3xl font-bold leading-tight text-white">{s.value}</p>
                <p className="text-[10px] text-sky-100/80">{s.sub}</p>
              </div>
            ))}
          </div>
        </div>
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
        <div
          className="fixed inset-x-2 bottom-28 z-40 lg:inset-x-auto lg:bottom-16 lg:right-4 lg:z-30 lg:w-[384px]"
          style={{ maxHeight: "min(62vh, 640px)" }}
        >
          <HotspotDetailPanel hotspotId={selected} onClose={() => setSelected(null)} />
        </div>
      )}
    </div>
  );
}
