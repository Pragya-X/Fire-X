"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, History, Pause, Play } from "lucide-react";
import { getHistorical, getPlayback } from "@/lib/api";
import type { Hotspot, PlaybackFrame } from "@/lib/types";
import { Button, Card, CardBody, CardHeader, CardTitle, ErrorState, Input, Select, Skeleton, Tabs } from "@/components/ui/primitives";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { DataTable, type Column } from "@/components/data-table";
import { fmtDt } from "@/lib/utils";

const MapView = dynamic(() => import("@/components/map/map-view").then((m) => m.MapView), { ssr: false, loading: () => <Skeleton className="h-72" /> });

const CLASSIFICATIONS = ["Industrial Fire", "Persistent Industrial Heat Source", "Gas Flare", "Wildfire", "Agricultural Burning", "Other Thermal Anomaly"];

export default function HistoricalPage() {
  const router = useRouter();
  const [tab, setTab] = useState("records");
  const [rows, setRows] = useState<Hotspot[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [state, setState] = useState("");
  const [classification, setClassification] = useState("");
  const [risk, setRisk] = useState("");

  const [frames, setFrames] = useState<PlaybackFrame[]>([]);
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(false);

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
    } finally {
      setLoading(false);
    }
  }, [page, dateFrom, dateTo, state, classification, risk]);

  const loadPlayback = useCallback(async () => {
    const res = await getPlayback(14);
    setFrames(res.frames);
    setFrameIdx(res.frames.length - 1);
  }, []);

  useEffect(() => {
    if (tab === "records") loadRecords();
    else loadPlayback();
  }, [tab, loadRecords, loadPlayback]);

  // Playback animation
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => {
      setFrameIdx((i) => {
        if (i >= frames.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 1200);
    return () => clearInterval(t);
  }, [playing, frames.length]);

  const playbackGeojson = useMemo(() => {
    const frame = frames[frameIdx];
    if (!frame) return null;
    return {
      type: "FeatureCollection" as const,
      features: frame.hotspots.map((h) => ({
        type: "Feature" as const,
        geometry: { type: "Point" as const, coordinates: [h.longitude, h.latitude] },
        properties: {
          id: h.code, code: h.code, classification: h.classification, risk_level: h.risk_level,
          risk_score: h.risk_score, brightness: h.brightness, frp: h.frp, state: "",
        },
      })),
    };
  }, [frames, frameIdx]);

  const columns: Column<Hotspot>[] = [
    { key: "code", header: "ID", render: (h) => <span className="font-mono font-semibold text-sky-400">{h.code}</span> },
    { key: "classification", header: "Classification", render: (h) => <ClassificationBadge classification={h.classification} confidence={h.classification_confidence} /> },
    { key: "risk", header: "Risk", render: (h) => <RiskBadge level={h.risk_level} score={h.risk_score} /> },
    { key: "acquisition_time", header: "Detected", render: (h) => <span className="text-slate-600">{fmtDt(h.acquisition_time)}</span> },
    { key: "state", header: "State", render: (h) => <span>{h.state}</span> },
    { key: "district", header: "District", render: (h) => <span>{h.district}</span> },
    { key: "temporal_pattern", header: "Pattern", render: (h) => <span className="uppercase text-slate-600">{h.temporal_pattern}</span> },
    { key: "persistence_score", header: "Persistence", render: (h) => <span className="font-mono">{Math.round(h.persistence_score)}</span> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-700 tracking-tight">Historical Records</h1>
          <p className="text-xs text-slate-400">14-day detection archive · map playback · recurring hotspot analysis</p>
        </div>
        <Tabs tabs={[{ id: "records", label: "Records" }, { id: "playback", label: "Map playback" }]} active={tab} onChange={setTab} />
      </div>

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
                  {["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"].map((r) => <option key={r} value={r}>{r}</option>)}
                </Select>
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardBody className="p-0">
              {error ? <div className="p-6"><p className="text-sm text-critical">{error}</p></div> : (
                <DataTable columns={columns} rows={rows} total={total} page={page} pageSize={20} loading={loading} onPageChange={setPage} onRowClick={(h) => router.push(`/hotspots/${h.id}`)} />
              )}
            </CardBody>
          </Card>
        </>
      )}

      {tab === "playback" && (
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <CalendarDays className="h-4 w-4 text-accent" />
              {frames[frameIdx] ? `${frames[frameIdx].label} · ${frames[frameIdx].count} detections` : "Loading..."}
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-slate-400">Day {frameIdx + 1} / {frames.length}</span>
              <Button variant="outline" size="sm" onClick={() => setPlaying(!playing)}>
                {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                {playing ? "Pause" : "Play"}
              </Button>
            </div>
          </CardHeader>
          <CardBody className="p-0">
            <div className="relative h-[440px]">
              <MapView hotspots={playbackGeojson} className="h-full w-full" />
              <div className="pointer-events-none absolute bottom-3 left-1/2 z-10 w-64 -translate-x-1/2">
                <input
                  type="range"
                  min={0}
                  max={frames.length - 1}
                  value={frameIdx}
                  onChange={(e) => setFrameIdx(Number(e.target.value))}
                  className="w-full accent-sky-500"
                  aria-label="Playback timeline"
                />
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {tab === "playback" && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-1.5"><History className="h-4 w-4 text-accent" /> Recurring hotspots</CardTitle></CardHeader>
          <CardBody>
            <p className="mb-3 text-[11px] text-slate-400">Locations with repeated detections - candidates for persistent industrial heat sources.</p>
            <div className="grid grid-cols-1 gap-1.5 md:grid-cols-2">
              {rows.filter((h) => ["recurring", "persistent"].includes(h.temporal_pattern)).slice(0, 10).map((h) => (
                <button key={h.id} onClick={() => router.push(`/hotspots/${h.id}`)} className="flex items-center justify-between rounded border border-base-border/40 bg-base-raised/30 px-3 py-2 text-left hover:border-accent/50">
                  <span className="font-mono text-xs text-sky-400">{h.code}</span>
                  <span className="text-[10px] text-slate-600">{h.temporal_pattern} · {Math.round(h.persistence_score)} persistence</span>
                  <RiskBadge level={h.risk_level} score={h.risk_score} />
                </button>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}