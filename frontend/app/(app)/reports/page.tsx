"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Download, FileText, Filter, Newspaper } from "lucide-react";
import { downloadDailyReport, getHotspots, downloadHotspotReport } from "@/lib/api";
import type { Hotspot } from "@/lib/types";
import { Button, Card, CardBody, CardHeader, CardTitle, ErrorState, Input, Select, Skeleton, useToast } from "@/components/ui/primitives";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { download } from "@/lib/utils";

export default function ReportsPage() {
  const { push } = useToast();
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getHotspots({ page_size: 50, sort: "risk_score", order: "desc", search: search || undefined, risk: risk || undefined })
      .then((r) => setHotspots(r.items))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [search, risk]);
  useEffect(load, [load]);

  const daily = async () => {
    try {
      const blob = await downloadDailyReport();
      download("firex-daily-intelligence-report.pdf", blob);
      push({ title: "Daily report downloaded", message: "Generated from live hotspot data.", tone: "success" });
    } catch (e) {
      push({ title: "Report failed", message: e instanceof Error ? e.message : "Could not generate report", tone: "error" });
    }
  };

  const incident = async (h: Hotspot) => {
    try {
      const blob = await downloadHotspotReport(h.id);
      download(`${h.code}-incident-report.pdf`, blob);
      push({ title: "Incident report downloaded", message: `${h.code} PDF generated.`, tone: "success" });
    } catch (e) {
      push({ title: "Report failed", message: e instanceof Error ? e.message : "Could not generate report", tone: "error" });
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-bold text-secondary">Report Generation</h1>
        <p className="text-xs text-muted/70">Incident reports, daily intelligence briefings and zone reports as downloadable PDF</p>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Card>
          <CardBody className="flex items-center gap-4">
            <span className="rounded-md border border-base-border bg-base-raised p-3 text-accent"><FileText className="h-5 w-5" /></span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-secondary">Daily Intelligence Report</p>
              <p className="text-[11px] text-muted/70">Hotspot summary with classifications, risk and alert counts for the last 24 hours.</p>
            </div>
            <Button onClick={daily}><Download className="h-4 w-4" /> PDF</Button>
          </CardBody>
        </Card>
        <Card>
          <CardBody className="flex items-center gap-4">
            <span className="rounded-md border border-base-border bg-base-raised p-3 text-accent"><Newspaper className="h-5 w-5" /></span>
            <div className="flex-1">
              <p className="text-sm font-semibold text-secondary">Industrial Zone Reports</p>
              <p className="text-[11px] text-muted/70">Per-zone risk, hotspot proximity and population exposure - open the Industrial Zones page and use the report button.</p>
            </div>
            <Link href="/industrial-zones"><Button variant="outline">Open zones</Button></Link>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-1.5"><Filter className="h-4 w-4 text-accent" /> Incident reports by hotspot</CardTitle></CardHeader>
        <CardBody>
          <div className="mb-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Input placeholder="Search hotspot code / state..." value={search} onChange={(e) => setSearch(e.target.value)} />
            <Select value={risk} onChange={(e) => setRisk(e.target.value)}>
              <option value="">All risk levels</option>
              {["CRITICAL", "HIGH", "ELEVATED", "MODERATE", "LOW"].map((r) => <option key={r} value={r}>{r}</option>)}
            </Select>
          </div>
          {loading ? <Skeleton className="h-40" /> : error ? <ErrorState message={error} onRetry={load} /> : (
            <div className="space-y-1.5">
              {hotspots.length === 0 && <p className="py-6 text-center text-xs text-muted/70">No hotspots match.</p>}
              {hotspots.slice(0, 25).map((h) => (
                <div key={h.id} className="flex flex-wrap items-center gap-2 rounded-md border border-base-border/40 bg-base-raised/30 px-3 py-2">
                  <span className="font-mono text-xs font-semibold text-sky-400">{h.code}</span>
                  <ClassificationBadge classification={h.classification} confidence={h.classification_confidence} />
                  <RiskBadge level={h.risk_level} score={h.risk_score} />
                  <span className="ml-auto text-[10px] text-muted/70">{h.state} / {h.district}</span>
                  <Button variant="outline" size="sm" onClick={() => incident(h)}><Download className="h-3.5 w-3.5" /> Incident PDF</Button>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}