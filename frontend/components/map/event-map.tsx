"use client";
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { ThermalEvent } from "@/lib/api";

export default function EventMap({ events, onSelect }: { events: ThermalEvent[]; onSelect: (id: string) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const select = useRef(onSelect); select.current = onSelect;
  const [ready, setReady] = useState(false);
  const [heat, setHeat] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!container.current) return;
    let view: maplibregl.Map;
    try {
      view = new maplibregl.Map({ container: container.current, center: [79,22], zoom: 4,
        style: { version: 8, sources: { base: { type: "raster", tileSize: 256,
          tiles: [process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png?key=cb1_328h_1_73d0124bd69f096f2afe7cb4"], attribution: "© CARTO © OpenStreetMap" } },
          layers: [{ id: "base", type: "raster", source: "base" }] } });
    } catch { setError("Map unavailable. Use the event table below."); return; }
    map.current = view;
    view.addControl(new maplibregl.NavigationControl());
    view.on("load", () => {
      view.addSource("events", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      view.addLayer({ id: "event-density", type: "heatmap", source: "events", layout: { visibility: "none" },
        paint: { "heatmap-weight": 1, "heatmap-radius": 30, "heatmap-opacity": .65 } });
      view.addLayer({ id: "events", type: "circle", source: "events", paint: { "circle-color": "#38bdf8", "circle-radius": 6, "circle-stroke-width": 1, "circle-stroke-color": "#fff" } });
      setReady(true);
    });
    view.on("click", "events", e => { const id = e.features?.[0]?.properties?.event_id; if (id) select.current(String(id)); });
    const observer = new ResizeObserver(() => view.resize()); observer.observe(container.current);
    return () => { observer.disconnect(); view.remove(); map.current = null; };
  }, []);
  useEffect(() => {
    const view = map.current; if (!view || !ready) return;
    (view.getSource("events") as maplibregl.GeoJSONSource).setData({ type: "FeatureCollection", features: events.map(e => ({
      type: "Feature", geometry: { type: "Point", coordinates: [e.longitude,e.latitude] }, properties: { event_id: e.event_id } })) });
    if (events.length) {
      const bounds = new maplibregl.LngLatBounds(); events.forEach(e => bounds.extend([e.longitude,e.latitude]));
      view.fitBounds(bounds, { padding: 45, maxZoom: 10, duration: 600 });
    }
  }, [events, ready]);
  useEffect(() => { if (ready) map.current?.setLayoutProperty("event-density","visibility",heat ? "visible" : "none"); }, [heat,ready]);
  return <div className="relative h-80 overflow-hidden rounded-lg border border-base-border">
    <div ref={container} className="absolute inset-0" aria-label="Observed thermal events map" />
    <label className="absolute left-3 top-3 rounded bg-base-raised p-2 text-xs"><input type="checkbox" checked={heat} onChange={e => setHeat(e.target.checked)} /> Event density heatmap</label>
    <p className="absolute bottom-2 left-3 rounded bg-base-raised p-1 text-xs">{error || "Observed locations · density is not fire risk · no demo reference overlays"}</p>
  </div>;
}
