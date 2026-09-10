"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Activity, BarChart3, Brain, Building2, Flame, TrendingUp } from "lucide-react";
import { getAnalytics } from "@/lib/api";
import type { AnalyticsData } from "@/lib/types";
import { Card, CardBody, CardHeader, CardTitle, ErrorState, Skeleton } from "@/components/ui/primitives";

const CLASS_COLORS: Record<string, string> = {
  "Industrial Fire": "#ef4444",
  "Persistent Industrial Heat Source": "#3b82f6",
  "Gas Flare": "#a855f7",
  Wildfire: "#f97316",
  "Agricultural Burning": "#eab308",
  "Other Thermal Anomaly": "#64748b",
};

const tooltipStyle = {
  background: "#0a101c",
  border: "1px solid #1e293b",
  borderRadius: 8,
  fontSize: 11,
  color: "#e2e8f0",
};

function ChartCard({ title, icon, children, className }: { title: string; icon?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5">{icon}{title}</CardTitle>
      </CardHeader>
      <CardBody className="h-72">{children}</CardBody>
    </Card>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    getAnalytics().then(setData).catch((e: Error) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  if (error) return <ErrorState message={`Analytics unavailable: ${error}`} onRetry={load} />;
  if (!data) return <div className="grid grid-cols-1 gap-4 lg:grid-cols-3"><Skeleton className="h-72" /><Skeleton className="h-72" /><Skeleton className="h-72" /></div>;

  const summary = [
    { label: "Avg classification confidence", value: `${data.avg_classification_confidence}%`, icon: <Brain className="h-4 w-4" /> },
    { label: "Avg risk score", value: `${data.avg_risk_score}`, icon: <TrendingUp className="h-4 w-4" /> },
    { label: "Alerts open", value: String(Object.values(data.alert_status).reduce((a, b) => a + b, 0)), icon: <Activity className="h-4 w-4" /> },
    { label: "Top zone risk", value: data.top_industrial_zones[0]?.risk_level ?? "-", icon: <Building2 className="h-4 w-4" /> },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-secondary tracking-tight">Analytics</h1>
        <p className="text-xs text-muted/70">All charts are computed from live database aggregations - generated {new Date(data.generated_at).toLocaleString("en-IN")}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {summary.map((s) => (
          <Card key={s.label} className="px-4 py-3">
            <div className="flex items-center gap-2 text-[11px] text-muted/70">{s.icon}{s.label}</div>
            <p className="mt-1 font-mono text-2xl font-bold text-secondary">{s.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard title="Hotspots by classification" icon={<Flame className="h-4 w-4 text-accent" />}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data.by_classification} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={45} paddingAngle={2}>
                {data.by_classification.map((c) => <Cell key={c.name} fill={CLASS_COLORS[c.name] || "#64748b"} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Hotspots by risk level" icon={<BarChart3 className="h-4 w-4 text-accent" />}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.by_risk} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(148,163,184,0.08)" }} />
              <Bar dataKey="value" name="Hotspots" radius={[4, 4, 0, 0]}>
                {data.by_risk.map((r) => (
                  <Cell key={r.name} fill={r.name === "CRITICAL" ? "#ef4444" : r.name === "HIGH" ? "#f97316" : r.name === "ELEVATED" ? "#eab308" : r.name === "MODERATE" ? "#3b82f6" : "#22c55e"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Daily detections (14 days)" icon={<Activity className="h-4 w-4 text-accent" />}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.daily} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="dailyGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.6} />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="count" name="Detections" stroke="#38bdf8" fill="url(#dailyGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <ChartCard title="Hotspots by state" icon={<BarChart3 className="h-4 w-4 text-accent" />}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.by_state} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 9, fill: "#94a3b8" }} />
              <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 9, fill: "#94a3b8" }} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(148,163,184,0.08)" }} />
              <Bar dataKey="value" name="Hotspots" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Industrial vs wildfire trend" icon={<Flame className="h-4 w-4 text-accent" />}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.industrial_vs_wildfire} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 8, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="industrial" name="Industrial" stroke="#ef4444" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="wildfire" name="Wildfire" stroke="#f97316" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Classification trend (14 days)" icon={<Brain className="h-4 w-4 text-accent" />}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.classification_series} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 8, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 9 }} />
              <Area type="monotone" dataKey="Wildfire" stackId="1" stroke="#f97316" fill="#f9731655" />
              <Area type="monotone" dataKey="Agricultural Burning" stackId="1" stroke="#eab308" fill="#eab30844" />
              <Area type="monotone" dataKey="Industrial Fire" stackId="1" stroke="#ef4444" fill="#ef444444" />
              <Area type="monotone" dataKey="Persistent Industrial Heat Source" stackId="1" stroke="#3b82f6" fill="#3b82f644" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Top industrial zones by risk" icon={<Building2 className="h-4 w-4 text-accent" />}>
          <div className="flex h-full flex-col justify-center gap-2 overflow-y-auto">
            {data.top_industrial_zones.map((z, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-6 font-mono text-xs text-muted/70">{i + 1}</span>
                <span className="flex-1 truncate text-xs text-secondary">{z.name}</span>
                <span className="text-[10px] text-muted/70">{z.type}</span>
                <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${z.risk_level === "CRITICAL" ? "border-critical/40 text-critical" : z.risk_level === "HIGH" ? "border-high/40 text-high" : z.risk_level === "ELEVATED" ? "border-moderate/40 text-moderate" : "border-low/40 text-low"}`}>
                  {z.risk_level}
                </span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Top recurring hotspots" icon={<Activity className="h-4 w-4 text-accent" />}>
          <div className="flex h-full flex-col justify-center gap-2 overflow-y-auto">
            {data.top_recurring_hotspots.map((h, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-16 font-mono text-xs text-sky-400">{h.code}</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-base-panel">
                  <div className="h-full rounded-full bg-sky-500/70" style={{ width: `${h.persistence_score}%` }} />
                </div>
                <span className="w-9 text-right font-mono text-[10px] text-muted">{Math.round(h.persistence_score)}</span>
                <span className="hidden w-40 truncate text-[10px] text-muted/70 sm:block">{h.classification}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </div>
  );
}