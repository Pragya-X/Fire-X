"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, Search, X } from "lucide-react";
import { getHotspots, downloadExport } from "@/lib/api";
import type { Hotspot } from "@/lib/types";
import { Button, Card, CardBody, CardHeader, CardTitle, Input, Select, useToast } from "@/components/ui/primitives";
import { ClassificationBadge, RiskBadge } from "@/components/badges";
import { DataTable, type Column } from "@/components/data-table";
import { download, fmt, fmtDt } from "@/lib/utils";

const CLASSIFICATIONS = [
  "Industrial Fire",
  "Persistent Industrial Heat Source",
  "Gas Flare",
  "Wildfire",
  "Agricultural Burning",
  "Other Thermal Anomaly",
];
const RISKS = ["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"];

export default function HotspotsPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { push } = useToast();

  const [rows, setRows] = useState<Hotspot[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [sortKey, setSortKey] = useState("acquisition_time");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // filters
  const [classification, setClassification] = useState(params.get("classification") ?? "");
  const [risk, setRisk] = useState("");
  const [minConfidence, setMinConfidence] = useState("");
  const [state, setState] = useState("");
  const [district, setDistrict] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [industrialProx, setIndustrialProx] = useState("");
  const [forestProx, setForestProx] = useState("");
  const [agriProx, setAgriProx] = useState("");
  const [settlementProx, setSettlementProx] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getHotspots({
        page, page_size: pageSize, classification: classification || undefined, risk: risk || undefined,
        min_confidence: minConfidence ? Number(minConfidence) : undefined,
        state: state || undefined, district: district || undefined,
        date_from: dateFrom || undefined, date_to: dateTo || undefined,
        industrial_proximity: industrialProx ? Number(industrialProx) : undefined,
        forest_proximity: forestProx ? Number(forestProx) : undefined,
        agriculture_proximity: agriProx ? Number(agriProx) : undefined,
        settlement_proximity: settlementProx ? Number(settlementProx) : undefined,
        search: search || undefined, sort: sortKey, order: sortOrder,
      });
      setRows(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load hotspots");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, classification, risk, minConfidence, state, district, dateFrom, dateTo, industrialProx, forestProx, agriProx, settlementProx, search, sortKey, sortOrder]);

  useEffect(() => { load(); }, [load]);

  const activeFilters = useMemo(
    () => [classification, risk, minConfidence, state, district, dateFrom, dateTo, industrialProx, forestProx, agriProx, settlementProx, search].filter(Boolean).length,
    [classification, risk, minConfidence, state, district, dateFrom, dateTo, industrialProx, forestProx, agriProx, settlementProx, search]
  );

  const clearFilters = () => {
    setClassification(""); setRisk(""); setMinConfidence(""); setState(""); setDistrict("");
    setDateFrom(""); setDateTo(""); setIndustrialProx(""); setForestProx(""); setAgriProx(""); setSettlementProx("");
    setSearch(""); setSearchInput(""); setPage(1);
  };

  const doExport = async (format: "csv" | "json" | "geojson" | "pdf") => {
    try {
      const blob = await downloadExport(format, {
        classification: classification || "", risk: risk || "", state: state || "",
      });
      download(`firex-hotspots.${format === "geojson" ? "geojson" : format}`, blob);
      push({ title: `Export complete`, message: `${total} hotspots exported as ${format.toUpperCase()}.`, tone: "success" });
    } catch (e) {
      push({ title: "Export failed", message: e instanceof Error ? e.message : "Could not export", tone: "error" });
    }
  };

  const columns: Column<Hotspot>[] = [
    { key: "code", header: "ID", render: (h) => <span className="font-mono font-semibold text-sky-400">{h.code}</span> },
    { key: "classification", header: "Classification", render: (h) => <ClassificationBadge classification={h.classification} confidence={h.classification_confidence} /> },
    { key: "risk", header: "Risk", render: (h) => <RiskBadge level={h.risk_level} score={h.risk_score} /> },
    { key: "confidence", header: "Confidence", render: (h) => <span className="font-mono">{Math.round(h.classification_confidence * 100)}%</span> },
    { key: "brightness", header: "Brightness", render: (h) => <span className="font-mono">{fmt(h.brightness)} K</span>, hideOnMobile: true },
    { key: "frp", header: "FRP", render: (h) => <span className="font-mono">{fmt(h.frp, 1)} MW</span>, hideOnMobile: true },
    { key: "latitude", header: "Latitude", render: (h) => <span className="font-mono text-muted">{h.latitude.toFixed(4)}</span>, hideOnMobile: true },
    { key: "longitude", header: "Longitude", render: (h) => <span className="font-mono text-muted">{h.longitude.toFixed(4)}</span>, hideOnMobile: true },
    { key: "state", header: "State", render: (h) => <span>{h.state}</span>, hideOnMobile: true },
    { key: "district", header: "District", render: (h) => <span>{h.district}</span>, hideOnMobile: true },
    { key: "acquisition_time", header: "Detected", render: (h) => <span className="text-muted">{fmtDt(h.acquisition_time)}</span>, hideOnMobile: true },
    { key: "persistence_score", header: "Persistence", render: (h) => <span className="font-mono">{Math.round(h.persistence_score)}</span>, hideOnMobile: true },
    { key: "status", header: "Status", render: (h) => <span className="uppercase text-muted">{h.status}</span>, hideOnMobile: true },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-secondary tracking-tight">Hotspot Intelligence</h1>
          <p className="text-xs text-muted/70 mt-0.5">{total.toLocaleString()} detections · click a row for full intelligence dossier</p>
        </div>
        <div className="flex gap-2">
          {(["csv", "json", "geojson", "pdf"] as const).map((f) => (
            <Button key={f} variant="outline" size="sm" onClick={() => doExport(f)}>
              <Download className="h-3.5 w-3.5" /> {f.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters {activeFilters > 0 && <span className="text-accent">({activeFilters} active)</span>}</CardTitle>
          {activeFilters > 0 && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-3 w-3" /> Clear all
            </Button>
          )}
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted/70" />
              <Input
                className="pl-8"
                placeholder="Search code/state..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput)}
              />
            </div>
            <Select value={classification} onChange={(e) => { setClassification(e.target.value); setPage(1); }}>
              <option value="">Classification</option>
              {CLASSIFICATIONS.map((c) => <option key={c} value={c}>{c}</option>)}
            </Select>
            <Select value={risk} onChange={(e) => { setRisk(e.target.value); setPage(1); }}>
              <option value="">Risk level</option>
              {RISKS.map((r) => <option key={r} value={r}>{r}</option>)}
            </Select>
            <Input placeholder="Min confidence (0-1)" value={minConfidence} onChange={(e) => setMinConfidence(e.target.value)} />
            <Input placeholder="State" value={state} onChange={(e) => setState(e.target.value)} />
            <Input placeholder="District" value={district} onChange={(e) => setDistrict(e.target.value)} />
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} aria-label="Date from" />
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} aria-label="Date to" />
            <Input placeholder="Within km of industry" value={industrialProx} onChange={(e) => setIndustrialProx(e.target.value)} />
            <Input placeholder="Within km of forest" value={forestProx} onChange={(e) => setForestProx(e.target.value)} />
            <Input placeholder="Within km of agriculture" value={agriProx} onChange={(e) => setAgriProx(e.target.value)} />
            <Input placeholder="Within km of settlement" value={settlementProx} onChange={(e) => setSettlementProx(e.target.value)} />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody className="p-0">
          {error ? (
            <div className="p-6"><p className="text-sm text-critical">{error}</p></div>
          ) : (
            <DataTable
              columns={columns}
              rows={rows}
              total={total}
              page={page}
              pageSize={pageSize}
              loading={loading}
              onPageChange={setPage}
              onSort={(key) => {
                if (sortKey === key) setSortOrder(sortOrder === "asc" ? "desc" : "asc");
                else { setSortKey(key); setSortOrder("desc"); }
              }}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onRowClick={(h) => router.push(`/hotspots/${h.id}`)}
            />
          )}
        </CardBody>
      </Card>
    </div>
  );
}