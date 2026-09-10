"use client";
import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getEventStatus, getThermalEvents, getThermalEvent, getEventFacility, saveEventAnnotation, exportEventAnnotations, getEventExplanation } from "@/lib/api";
import type { ThermalEvent, EventDetail, EventAnnotation } from "@/lib/api";
import { useAuth } from "@/lib/auth";
const EventMap = dynamic(() => import("@/components/map/event-map"), { ssr: false });
const box = "rounded-lg border border-base-border bg-base-raised p-4";
const input = "rounded border border-base-border bg-white px-2 py-1 text-sm text-slate-700";
const button = "rounded border border-slate-600 px-3 py-1.5 text-sm hover:bg-base-panel disabled:opacity-40";
const emptyForm = { label: "Unknown", confidence: "", quality: "C" as "A" | "B" | "C", source: "", evidence: "", notes: "" };
function value(v: unknown) { return v === null || v === undefined ? "Unavailable" : typeof v === "number" ? v.toFixed(3) : String(v); }
function download(name: string, payload: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
}

export default function EventWorkspace() {
  const { user } = useAuth();
  const [status,setStatus] = useState<Awaited<ReturnType<typeof getEventStatus>> | null>(null);
  const [events,setEvents] = useState<ThermalEvent[]>([]);
  const [total,setTotal] = useState(0);
  const [detail,setDetail] = useState<EventDetail | null>(null);
  const [selection,setSelection] = useState("");
  const [facility,setFacility] = useState<ThermalEvent[] | null>(null);
  const [explanation,setExplanation] = useState<Awaited<ReturnType<typeof getEventExplanation>> | null>(null);
  const [explaining,setExplaining] = useState(false);
  const [comparison,setComparison] = useState("");
  const [error,setError] = useState(""); const [message,setMessage] = useState("");
  const [loading,setLoading] = useState(true); const [saving,setSaving] = useState(false);
  const [from,setFrom] = useState(""); const [to,setTo] = useState(""); const [facilityFilter,setFacilityFilter] = useState("");
  const [frame,setFrame] = useState(0); const [playing,setPlaying] = useState(false);
  const [form,setForm] = useState(emptyForm);
  const canAnnotate = ["analyst","admin"].includes(user?.role || "");
  async function load() {
    setLoading(true); setError("");
    try {
      const query: Record<string,string> = { limit: "1000" };
      if (from) query.date_from = `${from}T00:00:00Z`;
      if (to) query.date_to = `${to}T23:59:59Z`;
      if (facilityFilter) query.facility_id = facilityFilter;
      const [s,r] = await Promise.all([getEventStatus(),getThermalEvents(query)]);
      setStatus(s); setEvents(r.items); setTotal(r.total); setFrame(r.items.length); setPlaying(false);
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load events"); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []); // Initial load; filters apply explicitly.
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => setFrame(f => { if (f >= events.length) { setPlaying(false); return f; } return f+1; }),800);
    return () => clearInterval(timer);
  }, [playing,events.length]);
  useEffect(() => {
    let active = true; setDetail(null); setFacility(null); setExplanation(null); setForm(emptyForm); setMessage("");
    if (!selection) return;
    getThermalEvent(selection).then(d => {
      if (!active) return;
      setDetail(d); const latest = d.annotations.at(-1)?.annotation;
      if (latest) setForm({ label: latest.label, confidence: latest.confidence === null ? "" : String(latest.confidence), quality: latest.quality, source: latest.source, evidence: latest.evidence.join("\n"), notes: latest.notes });
    }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [selection]);
  const visible = useMemo(() => events.slice(0,frame),[events,frame]);
  const other = events.find(e => e.event_id === comparison);
  const last = detail?.annotations.at(-1);
  async function save(action: "save" | "submit" | "approve" | "reject") {
    if (!detail) return; setSaving(true); setError(""); setMessage("");
    try {
      await saveEventAnnotation(detail.event_id,{ expected_revision: last?.revision || 0, action, label: form.label,
        confidence: form.confidence === "" ? null : Number(form.confidence), quality: form.quality, source: form.source,
        evidence: form.evidence.split("\n").map(s => s.trim()).filter(Boolean),notes: form.notes });
      setDetail(await getThermalEvent(detail.event_id)); setMessage("Annotation revision saved.");
    } catch (e) { setError(e instanceof Error ? e.message : "Annotation failed"); } finally { setSaving(false); }
  }
  return <div className="space-y-4 text-slate-700">
    <div><h1 className="text-xl font-semibold">Event evidence workspace</h1><p className="text-sm text-slate-400">Review imported thermal observations and their supporting evidence.</p></div>
    {error && <p role="alert" className="rounded border border-red-300 p-3 text-red-600">{error}</p>}
    {message && <p role="status" className="text-sky-700">{message}</p>}
    <div className={box}><strong>Model: {status?.model_mode || "Unavailable"} · Training: {status?.training_ready ? "Ready" : "Blocked"}</strong><p className="mt-1 text-sm text-slate-400">{status?.reason || "Checking event model status…"}</p></div>
    <form className={`${box} flex flex-wrap items-end gap-3`} onSubmit={e => { e.preventDefault(); void load(); }}>
      <label className="grid gap-1 text-xs">From (UTC)<input className={input} type="date" value={from} onChange={e => setFrom(e.target.value)} /></label>
      <label className="grid gap-1 text-xs">Through (UTC)<input className={input} type="date" value={to} onChange={e => setTo(e.target.value)} /></label>
      <label className="grid gap-1 text-xs">Facility ID<input className={input} value={facilityFilter} onChange={e => setFacilityFilter(e.target.value)} /></label>
      <button className={button} disabled={loading}>Apply filters</button>
      <button type="button" className={button} onClick={() => download("thermal-events.json",{items:events,total,limit:1000,filters:{from,to,facilityFilter}})}>Export loaded events</button>
      <button type="button" className={button} onClick={() => exportEventAnnotations().then(a => download("annotations.json",a)).catch(e => setError(e.message))}>Export all annotations</button>
    </form>
    <p className="text-sm">{loading ? "Loading events…" : `${events.length} loaded of ${total} matching events · ${events.filter(e => e.intelligence?.anomaly.status === "elevated").length} elevated deviations · ${events.filter(e => e.intelligence?.persistence.status === "persistent_candidate").length} persistent candidates`}</p>
    {!loading && !error && !events.length && <div className={box}>No observations imported for these filters. An administrator must validate and import real event artifacts. Demo hotspots are available in the existing Command Center.</div>}
    <EventMap events={visible} onSelect={setSelection} />
    <div className="flex items-center gap-3"><button className={button} disabled={!events.length} onClick={() => { if (frame >= events.length) setFrame(0); setPlaying(p => !p); }}>{playing ? "Pause" : "Play timeline"}</button><input aria-label="Event timeline position" type="range" min={0} max={events.length} value={frame} onChange={e => { setPlaying(false); setFrame(Number(e.target.value)); }} className="flex-1" /><span className="text-xs">{frame}/{events.length}</span></div>
    <div className={`${box} max-h-72 overflow-auto`}><table className="w-full text-left text-xs"><thead><tr><th>Event</th><th>Start (UTC)</th><th>FRP mean (MW)</th><th>Decision</th><th>Confidence</th></tr></thead><tbody>{visible.map(e => <tr key={e.event_id} className="border-t border-base-border/40"><td><button className="py-2 text-sky-700 underline" onClick={() => setSelection(e.event_id)}>{e.event_id}</button></td><td>{e.start_time}</td><td>{value(e.features.mean_frp)}</td><td>{e.intelligence?.decision || "Unknown"}</td><td>{value(e.intelligence?.confidence)}</td></tr>)}</tbody></table></div>
    {selection && !detail && <p>Loading selected event…</p>}
    {detail && <>
      <section className={box}><h2 className="font-semibold">{detail.event_id}</h2><p className="text-sm">{detail.intelligence?.decision} · Confidence: {value(detail.intelligence?.confidence)} ({detail.intelligence?.confidence_type})</p><ul className="my-3 list-inside list-disc text-sm">{detail.intelligence?.reasons.map(r => <li key={r}>{r}</li>)}</ul>
        <p className="text-sm">SHAP: {detail.intelligence?.explanation.shap.reason || "Unavailable"}</p>
        <button className={`${button} my-2`} disabled={!canAnnotate || explaining} onClick={async () => { setExplaining(true); try { setExplanation(await getEventExplanation(detail.event_id)); } catch (e) { setError(e instanceof Error ? e.message : "Explanation unavailable"); } finally { setExplaining(false); } }}>Request model explanation</button>
        {explanation && <div className="text-xs"><p>{explanation.explanation.shap.reason || "SHAP probability contributions by feature and class"}</p>{explanation.explanation.shap.available && <pre className="max-h-64 overflow-auto">{JSON.stringify(explanation.explanation,null,2)}</pre>}</div>}
        <p className="text-sm">Historical mean FRP: {value(detail.intelligence?.anomaly.historical_mean_mw)} MW · Anomaly z-score: {value(detail.intelligence?.anomaly.score)} · Recurrence: {value(detail.intelligence?.persistence.observed_recurrence)}</p>
        <details className="mt-3 text-xs"><summary>Source provenance and full evidence</summary><pre className="mt-2 overflow-auto">{JSON.stringify({provenance:detail.provenance,features:detail.features,intelligence:detail.intelligence},null,2)}</pre></details>
      </section>
      <section className={box}><h2 className="font-semibold">Observed FRP timeline</h2><p className="text-xs text-slate-400">Event member detections, up to 1,000. Historical baseline is shown above.</p><div className="h-52"><ResponsiveContainer><LineChart data={detail.observations}><XAxis dataKey="acquisition_time" hide /><YAxis /><Tooltip /><Line type="linear" dataKey="frp" stroke="#38bdf8" connectNulls={false} isAnimationActive={false} /></LineChart></ResponsiveContainer></div>
        {detail.facility_id && <button className={button} onClick={() => getEventFacility(detail.facility_id!).then(r => setFacility(r.events)).catch(e => setError(e.message))}>Load nearest facility history</button>}
        {facility && <div className="mt-2 text-xs"><p>Nearest-reference association does not establish cause. Up to 1,000 events.</p>{facility.map(e => <button key={e.event_id} className="mr-3 underline" onClick={() => setSelection(e.event_id)}>{e.start_time} · {e.event_id}</button>)}</div>}
      </section>
      <section className={box}><h2 className="font-semibold">Compare event evidence</h2><select aria-label="Comparison event" className={`${input} my-2 max-w-full`} value={comparison} onChange={e => setComparison(e.target.value)}><option value="">Select another event</option>{events.filter(e => e.event_id!==detail.event_id).map(e => <option key={e.event_id}>{e.event_id}</option>)}</select>{other && <table className="w-full text-left text-sm"><thead><tr><th>Feature</th><th>Selected</th><th>Comparison</th></tr></thead><tbody>{["mean_frp","detection_count","active_days_90d","dist_nearest_industrial_km"].map(f => <tr key={f}><td>{f}</td><td>{value(detail.features[f])}</td><td>{value(other.features[f])}</td></tr>)}</tbody></table>}</section>
      <section className={box}><h2 className="font-semibold">Annotation · revision {last?.revision || 0} · {last?.annotation.review_status || "Unlabeled"}</h2><p className="mb-3 text-xs text-slate-400">Approval requires a different analyst, evidence, confidence and review time. Only approved A/B labels with confidence ≥0.8 can be eligible; Unknown is excluded.</p>
        <fieldset disabled={!canAnnotate || saving} className="grid gap-3 sm:grid-cols-2">
          <label className="grid gap-1 text-xs">Class<select className={input} value={form.label} onChange={e => setForm({...form,label:e.target.value})}>{status?.classes.map(c => <option key={c}>{c}</option>)}</select></label>
          <label className="grid gap-1 text-xs">Annotation confidence (0–1)<input className={input} type="number" min={0} max={1} step={.05} value={form.confidence} onChange={e => setForm({...form,confidence:e.target.value})} /></label>
          <label className="grid gap-1 text-xs">Quality<select className={input} value={form.quality} onChange={e => setForm({...form,quality:e.target.value as EventAnnotation["quality"]})}><option value="A">A · direct corroborated evidence</option><option value="B">B · strong indirect evidence</option><option value="C">C · weak or ambiguous evidence</option></select></label>
          <label className="grid gap-1 text-xs">Source<input className={input} value={form.source} onChange={e => setForm({...form,source:e.target.value})} /></label>
          <label className="grid gap-1 text-xs">Evidence references (one per line)<textarea className={input} value={form.evidence} onChange={e => setForm({...form,evidence:e.target.value})} /></label>
          <label className="grid gap-1 text-xs">Notes<textarea className={input} value={form.notes} onChange={e => setForm({...form,notes:e.target.value})} /></label>
          <div className="flex flex-wrap gap-2 sm:col-span-2"><button className={button} onClick={() => save("save")}>Save draft</button><button className={button} onClick={() => save("submit")}>Submit for review</button><button className={button} disabled={last?.annotation.review_status!=="submitted" || last?.annotation.annotator===String(user?.id)} onClick={() => save("approve")}>Approve submitted revision</button><button className={button} disabled={last?.annotation.review_status!=="submitted" || last?.annotation.annotator===String(user?.id)} onClick={() => save("reject")}>Reject submitted revision</button></div>
        </fieldset>{!canAnnotate && <p className="mt-2 text-xs">Analyst role required to annotate.</p>}
        <details className="mt-3 text-xs"><summary>Annotation revision history ({detail.annotations.length})</summary><pre className="overflow-auto">{JSON.stringify(detail.annotations,null,2)}</pre></details>
      </section>
    </>}
  </div>;
}
