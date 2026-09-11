"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, BarChart2, CalendarDays, ChevronRight, Clock,
  Flame, History, Info, MapPin, Pause, Play, RefreshCw,
} from "lucide-react";
import { getHistorical, getPlayback, getRecurring, getTimeline } from "@/lib/api";
import type { Hotspot, PlaybackFrame } from "@/lib/types";
import {
  Button, Card, CardBody, CardHeader, CardTitle, Input, Select, Skeleton, Tabs,
} from "@/components/ui/primitives";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { DataTable, type Column } from "@/components/data-table";
import { fmtDt } from "@/lib/utils";

const MapView = dynamic(
  () => import("@/components/map/map-view").then((m) => m.MapView),
  { ssr: false, loading: () => <Skeleton className="h-72" /> }
);

const CLASSIFICATIONS = [
  "Industrial Fire",
  "Persistent Industrial Heat Source",
  "Gas Flare",
  "Wildfire",
  "Agricultural Burning",
  "Other Thermal Anomaly",
];

const RISK_COLORS: Record<string, string> = {
  CRITICAL: "#ef4444",
  HIGH: "#f97316",
  ELEVATED: "#eab308",
  MODERATE: "#3b82f6",
  LOW: "#22c55e",
};

const RISK_BG: Record<string, string> = {
  CRITICAL: "bg-red-500/15 text-red-400 border-red-500/30",
  HIGH: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  ELEVATED: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  MODERATE: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  LOW: "bg-green-500/15 text-green-400 border-green-500/30",
};

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-base-border/40">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="w-8 text-right font-mono text-[10px] text-muted">{value}</span>
    </div>
  );
}

function TimelineBar({ data }: { data: { date: string; count: number }[] }) {
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="flex items-end gap-0.5" style={{ height: 56 }}>
      {data.map((d) => {
        const h = Math.max(4, Math.round((d.count / max) * 56));
        const isToday = d.date === new Date().toISOString().slice(0, 10);
        return (
          <div
            key={d.date}
            title={`${d.date}: ${d.count} detections`}
            className="group relative flex-1 cursor-default rounded-t transition-all duration-200 hover:brightness-125"
            style={{ height: h, background: isToday ? "#38bdf8" : "rgba(56,189,248,0.4)" }}
          >
            <div className="pointer-events-none absolute -top-8 left-1/2 z-10 hidden -translate-x-1/2 whitespace-nowrap rounded bg-base-panel px-1.5 py-0.5 text-[9px] text-primary shadow group-hover:block">
              {d.count}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function HistoricalPage() {
  const router = useRouter();
  const [tab, setTab] = useState("overview");

  // Overview
  const [timeline, setTimeline] = useState<{ date: string; count: number }[]>([]);
  const [recurring, setRecurring] = useState<Hotspot[]>([]);
  const [loadingOverview, setLoadingOverview] = useState(true);

  // Records
  const [rows, setRows] = useState<Hotspot[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [state, setState] = useState("");
  const [classification, setClassification] = useState("");
  const [risk, setRisk] = useState("");

  // Playback
  const [frames, setFrames] = useState<PlaybackFrame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loadingPlayback, setLoadingPlayback] = useState(false);

  const loadOverview = useCallback(async () => {
    setLoadingOverview(true);
    try {
      const [tl, rec] = await Promise.all([getTimeline(30), getRecurring()]);
      setTimeline(tl.timeline);
      setRecurring(rec.items);
    } catch { /* silently fail */ }
    finally { setLoadingOverview(false); }
  }, []);

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getHistorical({
        page: String(page), page_size: "20",
        date_from: dateFrom, date_to: dateTo, state, classification, risk,
      });
      setRows(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load historical records");
    } finally { setLoading(false); }
  }, [page, dateFrom, dateTo, state, classification, risk]);

  const loadPlayback = useCallback(async () => {
    setLoadingPlayback(true);
    try {
      const res = await getPlayback(14);
      setFrames(res.frames);
      setFrameIdx(res.frames.length - 1);
    } catch { /* silently */ }
    finally { setLoadingPlayback(false); }
  }, []);

  useEffect(() => { loadOverview(); }, [loadOverview]);

  useEffect(() => {
    if (tab === "records") loadRecords();
    else if (tab === "playback") loadPlayback();
  }, [tab, loadRecords, loadPlayback]);

  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => {
      setFrameIdx((i) => {
        if (i >= frames.length - 1) { setPlaying(false); return i; }
        return i + 1;
      });
    }, 1200);
    return () => clearInterval(t);
  }, [playing, frames.length]);

  const totalDetections = useMemo(() => timeline.reduce((s, d) => s + d.count, 0), [timeline]);
  const avgPerDay = useMemo(() => timeline.length ? Math.round(totalDetections / timeline.length) : 0, [totalDetections, timeline]);
  const peakDay = useMemo(() => [...timeline].sort((a, b) => b.count - a.count)[0], [timeline]);

  const stateBreakdown = useMemo(() => {
    const map: Record<string, number> = {};
    rows.forEach((h) => { map[h.state || "Unknown"] = (map[h.state || "Unknown"] || 0) + 1; });
    return Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, 8);
  }, [rows]);

  const classBreakdown = useMemo(() => {
    const map: Record<string, number> = {};
    recurring.forEach((h) => { map[h.classification] = (map[h.classification] || 0) + 1; });
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }, [recurring]);

  const riskBreakdown = useMemo(() => {
    const map: Record<string, number> = {};
    recurring.forEach((h) => { map[h.risk_level] = (map[h.risk_level] || 0) + 1; });
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }, [recurring]);

  const playbackGeojson = useMemo(() => {
    const frame = frames[frameIdx];
    if (!frame) return null;
    return {
      type: "FeatureCollection" as const,
      features: frame.hotspots.map((h) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [h.longitude, h.latitude] },
        properties: {
          id: h.code, code: h.code, classification: h.classification,
          risk_level: h.risk_level, risk_score: h.risk_score,
          brightness: h.brightness, frp: h.frp, state: "",
        },
      })),
    };
  }, [frames, frameIdx]);

  const columns: Column<Hotspot>[] = [
    { key: "code", header: "ID", render: (h) => <span className="font-mono font-semibold text-sky-400">{h.code}</span> },
    { key: "classification", header: "Classification", render: (h) => <ClassificationBadge classification={h.classification} confidence={h.classification_confidence} /> },
    { key: "risk", header: "Risk", render: (h) => <RiskBadge level={h.risk_level} score={h.risk_score} /> },
    { key: "acquisition_time", header: "Detected", render: (h) => <span className="text-muted">{fmtDt(h.acquisition_time)}</span> },
    { key: "state", header: "State", render: (h) => <span>{h.state}</span> },
    { key: "district", header: "District", render: (h) => <span>{h.district}</span> },
    { key: "temporal_pattern", header: "Pattern", render: (h) => <span className="uppercase text-muted">{h.temporal_pattern}</span> },
    { key: "persistence_score", header: "Persistence", render: (h) => <span className="font-mono">{Math.round(h.persistence_score)}</span> },
  ];

  const maxStateCount = stateBreakdown[0]?.[1] ?? 1;
  const maxClassCount = classBreakdown[0]?.[1] ?? 1;
  const maxRiskCount = riskBreakdown[0]?.[1] ?? 1;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-secondary">Incident History</h1>
          <p className="mt-0.5 text-xs text-muted/70">
            30-day detection archive Â· recurring hotspot analysis Â· geographic breakdown Â· map playback
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Tabs
            tabs={[
              { id: "overview", label: "Overview" },
              { id: "records", label: "Records" },
              { id: "recurring", label: "Recurring" },
              { id: "playback", label: "Map Playback" },
            ]}
            active={tab}
            onChange={setTab}
          />
          <Button variant="ghost" size="sm" onClick={loadOverview} title="Refresh">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* OVERVIEW TAB */}
      {tab === "overview" && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {loadingOverview ? (
              Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)
            ) : (
              <>
                <Card className="px-4 py-3">
                  <p className="text-[9px] uppercase tracking-wider text-muted/60">Total (30 days)</p>
                  <p className="mt-1 text-2xl font-bold text-primary">{totalDetections.toLocaleString()}</p>
                  <p className="mt-0.5 text-[10px] text-muted/60">fire detections</p>
                </Card>
                <Card className="px-4 py-3">
                  <p className="text-[9px] uppercase tracking-wider text-muted/60">Daily average</p>
                  <p className="mt-1 text-2xl font-bold text-sky-400">{avgPerDay}</p>
                  <p className="mt-0.5 text-[10px] text-muted/60">detections / day</p>
                </Card>
                <Card className="px-4 py-3">
                  <p className="text-[9px] uppercase tracking-wider text-muted/60">Peak day</p>
                  <p className="mt-1 text-2xl font-bold text-orange-400">{peakDay?.count ?? 0}</p>
                  <p className="mt-0.5 text-[10px] text-muted/60">{peakDay?.date ?? "â€”"}</p>
                </Card>
                <Card className="px-4 py-3">
                  <p className="text-[9px] uppercase tracking-wider text-muted/60">Recurring hotspots</p>
                  <p className="mt-1 text-2xl font-bold text-red-400">{recurring.length}</p>
                  <p className="mt-0.5 text-[10px] text-muted/60">persistent sources</p>
                </Card>
              </>
            )}
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <BarChart2 className="h-4 w-4 text-accent" /> 30-day detection timeline
              </CardTitle>
              <span className="text-[10px] text-muted/60">daily fire incident count</span>
            </CardHeader>
            <CardBody>
              {loadingOverview ? (
                <Skeleton className="h-16" />
              ) : timeline.length === 0 ? (
                <p className="py-4 text-center text-xs text-muted/60">No timeline data available.</p>
              ) : (
                <>
                  <TimelineBar data={timeline} />
                  <div className="mt-2 flex justify-between text-[9px] text-muted/50">
                    <span>{timeline[0]?.date}</span>
                    <span>{timeline[Math.floor(timeline.length / 2)]?.date}</span>
                    <span>{timeline[timeline.length - 1]?.date}</span>
                  </div>
                </>
              )}
            </CardBody>
          </Card>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-1.5">
                  <Flame className="h-4 w-4 text-accent" /> Classification breakdown
                </CardTitle>
              </CardHeader>
              <CardBody>
                {loadingOverview ? <Skeleton className="h-32" /> : classBreakdown.length === 0 ? (
                  <p className="text-xs text-muted/60">No data available.</p>
                ) : (
                  <div className="space-y-2.5">
                    {classBreakdown.map(([cls, cnt]) => (
                      <div key={cls}>
                        <p className="mb-1 text-[11px] text-muted/80">{cls}</p>
                        <MiniBar value={cnt} max={maxClassCount} color="#38bdf8" />
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4 text-accent" /> Risk level breakdown
                </CardTitle>
              </CardHeader>
              <CardBody>
                {loadingOverview ? <Skeleton className="h-32" /> : riskBreakdown.length === 0 ? (
                  <p className="text-xs text-muted/60">No data available.</p>
                ) : (
                  <div className="space-y-2.5">
                    {riskBreakdown.map(([lvl, cnt]) => (
                      <div key={lvl}>
                        <span className={`mb-1 inline-flex rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider ${RISK_BG[lvl] ?? ""}`}>
                          {lvl}
                        </span>
                        <MiniBar value={cnt} max={maxRiskCount} color={RISK_COLORS[lvl] ?? "#64748b"} />
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <History className="h-4 w-4 text-accent" /> Recent critical incidents
              </CardTitle>
              <button className="text-[10px] text-accent hover:underline" onClick={() => setTab("records")}>
                View all records â†’
              </button>
            </CardHeader>
            <CardBody className="p-0">
              {loadingOverview ? <Skeleton className="m-4 h-32" /> : recurring.slice(0, 8).length === 0 ? (
                <p className="py-6 text-center text-xs text-muted/60">No recent incidents.</p>
              ) : (
                <div className="divide-y divide-base-border/40">
                  {recurring.slice(0, 8).map((h) => (
                    <button
                      key={h.id}
                      onClick={() => router.push(`/hotspots/${h.id}`)}
                      className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-base-raised/40"
                    >
                      <span className="font-mono text-xs font-bold text-sky-400">{h.code}</span>
                      <ClassificationBadge classification={h.classification} confidence={h.classification_confidence} />
                      <div className="flex flex-1 items-center gap-1.5 text-[11px] text-muted/70">
                        <MapPin className="h-3 w-3 shrink-0" />
                        {h.state}, {h.district}
                      </div>
                      <span className="text-[10px] text-muted/50">{fmtDt(h.acquisition_time)}</span>
                      <RiskBadge level={h.risk_level} score={h.risk_score} />
                      <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted/40" />
                    </button>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        </>
      )}

      {/* RECORDS TAB */}
      {tab === "records" && (
        <>
          <Card>
            <CardBody>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
                <Input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} aria-label="Date from" />
                <Input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} aria-label="Date to" />
                <Input placeholder="State" value={state} onChange={(e) => { setState(e.target.value); setPage(1); }} />
                <Select value={classification} onChange={(e) => { setClassification(e.target.value); setPage(1); }}>
                  <option value="">Classification</option>
                  {CLASSIFICATIONS.map((c) => <option key={c} value={c}>{c}</option>)}
                </Select>
                <Select value={risk} onChange={(e) => { setRisk(e.target.value); setPage(1); }}>
                  <option value="">Risk level</option>
                  {["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"].map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </Select>
              </div>
            </CardBody>
          </Card>

          {stateBreakdown.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-accent" /> Geographic breakdown (current filter)
                </CardTitle>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                  {stateBreakdown.map(([st, cnt]) => (
                    <div key={st}>
                      <p className="mb-1 text-[11px] text-muted/80">{st}</p>
                      <MiniBar value={cnt} max={maxStateCount} color="#38bdf8" />
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          )}

          <Card>
            <CardBody className="p-0">
              {error ? (
                <div className="p-6"><p className="text-sm text-critical">{error}</p></div>
              ) : (
                <DataTable
                  columns={columns} rows={rows} total={total} page={page} pageSize={20}
                  loading={loading} onPageChange={setPage}
                  onRowClick={(h) => router.push(`/hotspots/${h.id}`)}
                />
              )}
            </CardBody>
          </Card>
        </>
      )}

      {/* RECURRING TAB */}
      {tab === "recurring" && (
        <>
          <div className="flex items-start gap-3 rounded-lg border border-accent/20 bg-accent/5 px-4 py-3">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <div>
              <p className="text-xs font-semibold text-secondary">What are recurring hotspots?</p>
              <p className="mt-0.5 text-[11px] text-muted/70">
                Locations detected multiple times over the observation period. High persistence scores suggest industrial heat sources, gas flares, or uncontrolled fires that need field verification.
              </p>
            </div>
          </div>

          {loadingOverview ? <Skeleton className="h-64" /> : recurring.length === 0 ? (
            <Card><CardBody><p className="py-8 text-center text-xs text-muted/60">No recurring hotspots found.</p></CardBody></Card>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {recurring.map((h) => (
                <button
                  key={h.id}
                  onClick={() => router.push(`/hotspots/${h.id}`)}
                  className="group relative flex flex-col gap-2 rounded-lg border border-base-border/60 bg-base-panel px-4 py-3 text-left transition-all duration-150 hover:border-accent/40 hover:bg-base-raised/50 hover:shadow-lg"
                >
                  <div className="absolute left-0 top-0 h-full w-0.5 rounded-l-lg" style={{ background: RISK_COLORS[h.risk_level] ?? "#64748b" }} />
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="font-mono text-sm font-bold text-sky-400">{h.code}</span>
                      <div className="mt-1 flex flex-wrap items-center gap-1.5">
                        <ClassificationBadge classification={h.classification} confidence={h.classification_confidence} />
                        <RiskBadge level={h.risk_level} score={h.risk_score} />
                      </div>
                    </div>
                    <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted/30 transition-transform group-hover:translate-x-0.5 group-hover:text-accent" />
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-muted/60">
                    <MapPin className="h-3 w-3 shrink-0" />{h.state} Â· {h.district}
                  </div>
                  <div className="flex items-center gap-3 text-[10px]">
                    <span className="flex items-center gap-1 text-muted/60">
                      <Clock className="h-3 w-3" /> {fmtDt(h.acquisition_time)}
                    </span>
                    <span className="ml-auto rounded border border-base-border/40 bg-base-raised/50 px-1.5 py-0.5 font-mono text-[9px] uppercase text-muted/80">
                      {h.temporal_pattern}
                    </span>
                  </div>
                  <div>
                    <div className="mb-1 flex justify-between text-[9px] text-muted/50">
                      <span>Persistence score</span>
                      <span className="font-mono">{Math.round(h.persistence_score)}/100</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-base-border/40">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${Math.round(h.persistence_score)}%`,
                          background: h.persistence_score >= 70 ? "#ef4444" : h.persistence_score >= 40 ? "#f97316" : "#38bdf8",
                        }}
                      />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {/* PLAYBACK TAB */}
      {tab === "playback" && (
        <>
          <Card className="overflow-hidden">
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <CalendarDays className="h-4 w-4 text-accent" />
                {frames[frameIdx]
                  ? `${frames[frameIdx].label} Â· ${frames[frameIdx].count} detections`
                  : loadingPlayback ? "Loading..." : "14-day map playback"}
              </CardTitle>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted/70">Day {frameIdx + 1} / {frames.length}</span>
                <Button variant="outline" size="sm" onClick={() => setPlaying(!playing)} disabled={frames.length === 0}>
                  {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                  {playing ? "Pause" : "Play"}
                </Button>
              </div>
            </CardHeader>
            <CardBody className="p-0">
              {loadingPlayback ? <Skeleton className="h-[440px]" /> : (
                <div className="relative h-[440px]">
                  <MapView hotspots={playbackGeojson} className="h-full w-full" />
                  <div className="pointer-events-none absolute bottom-3 left-1/2 z-10 w-72 -translate-x-1/2">
                    <input
                      type="range" min={0} max={Math.max(frames.length - 1, 0)} value={frameIdx}
                      onChange={(e) => { setPlaying(false); setFrameIdx(Number(e.target.value)); }}
                      className="pointer-events-auto w-full accent-sky-500"
                      aria-label="Playback timeline"
                    />
                  </div>
                </div>
              )}
            </CardBody>
          </Card>

          {frames.length > 0 && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {frames.slice(-4).reverse().map((f) => (
                <Card key={f.label} className="px-3 py-2.5">
                  <p className="text-[9px] uppercase tracking-wider text-muted/60">{f.label}</p>
                  <p className="mt-1 text-xl font-bold text-primary">{f.count}</p>
                  <p className="text-[10px] text-muted/50">detections</p>
                </Card>
              ))}
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-1.5">
                <History className="h-4 w-4 text-accent" /> Recurring hotspots (14-day window)
              </CardTitle>
            </CardHeader>
            <CardBody>
              {loadingOverview ? <Skeleton className="h-32" /> : (
                <>
                  <p className="mb-3 text-[11px] text-muted/70">
                    Locations with repeated detections â€” candidates for persistent industrial heat sources.
                  </p>
                  <div className="grid grid-cols-1 gap-1.5 md:grid-cols-2">
                    {recurring.filter((h) => ["recurring", "persistent"].includes(h.temporal_pattern)).slice(0, 10).map((h) => (
                      <button
                        key={h.id}
                        onClick={() => router.push(`/hotspots/${h.id}`)}
                        className="flex items-center justify-between rounded border border-base-border/40 bg-base-raised/30 px-3 py-2 text-left hover:border-accent/50"
                      >
                        <span className="font-mono text-xs text-sky-400">{h.code}</span>
                        <span className="text-[10px] text-muted">{h.temporal_pattern} Â· {Math.round(h.persistence_score)} persistence</span>
                        <RiskBadge level={h.risk_level} score={h.risk_score} />
                      </button>
                    ))}
                    {recurring.filter((h) => ["recurring", "persistent"].includes(h.temporal_pattern)).length === 0 && (
                      <p className="col-span-2 py-4 text-center text-xs text-muted/60">No recurring hotspots in this window.</p>
                    )}
                  </div>
                </>
              )}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
