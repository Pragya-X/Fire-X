"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { getInfrastructureGeojson, getLandcoverGeojson, getNetworkGeojson, getZonesGeojson } from "@/lib/api";
import type { GeoJson, GeoJsonFeature } from "@/lib/types";
import { LayerControl } from "@/components/map/layer-control";
import { MapLegend } from "@/components/map/map-legend";
import { cn } from "@/lib/utils";

const escapeHtml = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

const LIGHT_TILES = process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png?key=cb1_328h_1_73d0124bd69f096f2afe7cb4";
const SATELLITE_TILES =
  process.env.NEXT_PUBLIC_SATELLITE_TILE_URL ||
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

const INDIA_BOUNDS: [[number, number], [number, number]] = [
  [66.5, 6.5],
  [97.5, 37.5],
];

export type LayerId =
  | "hotspots"
  | "heatmap"
  | "zones"
  | "refineries"
  | "factories"
  | "power"
  | "mines"
  | "settlements"
  | "forest"
  | "agriculture"
  | "roads"
  | "railways"
  | "pipelines";

export const DEFAULT_VISIBLE: Record<LayerId, boolean> = {
  hotspots: true,
  heatmap: false,
  zones: true,
  refineries: true,
  factories: true,
  power: true,
  mines: true,
  settlements: false,
  forest: true,
  agriculture: false,
  roads: false,
  railways: false,
  pipelines: true,
};

const RISK_COLORS: Record<string, string> = {
  CRITICAL: "#ef4444",
  HIGH: "#f97316",
  ELEVATED: "#eab308",
  MODERATE: "#3b82f6",
  LOW: "#22c55e",
};

const INFRA_STYLE: Record<string, { color: string; radius: number }> = {
  refinery: { color: "#38bdf8", radius: 5 },
  factory: { color: "#a78bfa", radius: 4 },
  power_plant: { color: "#fb923c", radius: 5 },
  mine: { color: "#f472b6", radius: 4 },
  settlement: { color: "#e2e8f0", radius: 3 },
  industrial_area: { color: "#38bdf8", radius: 4 },
};

const LANDCOVER_STYLE: Record<string, { color: string; opacity: number }> = {
  forest: { color: "#22c55e", opacity: 0.14 },
  agriculture: { color: "#a3e635", opacity: 0.16 },
};

const NETWORK_STYLE: Record<string, { color: string; width: number; opacity: number }> = {
  road: { color: "#64748b", width: 1.6, opacity: 0.8 },
  railway: { color: "#94a3b8", width: 1.4, opacity: 0.7 },
  pipeline: { color: "#facc15", width: 2.4, opacity: 0.9 },
};

// Map layer-id -> which visibility toggle controls it
const VISIBILITY_MAP: Record<LayerId, string[]> = {
  hotspots: ["hotspot-cluster", "hotspot-cluster-count", "hotspot-circle"],
  heatmap: ["risk-heat"],
  zones: ["zone-fill", "zone-outline", "zone-label"],
  refineries: ["infra-refinery-fill"],
  factories: ["infra-factory-fill"],
  power: ["infra-power_plant-fill"],
  mines: ["infra-mine-fill"],
  settlements: ["infra-settlement-fill"],
  forest: ["landcover-forest-fill", "landcover-forest-line"],
  agriculture: ["landcover-agriculture-fill", "landcover-agriculture-line"],
  roads: ["network-road"],
  railways: ["network-railway"],
  pipelines: ["network-pipeline"],
};

interface MapViewProps {
  hotspots?: GeoJson | null;
  selectedId?: number | null;
  onSelect?: (id: number, code: string) => void;
  focus?: { lat: number; lon: number; zoom?: number; key?: string } | null;
  className?: string;
}

function splitByProp(geojson: GeoJson | null, prop: string): Record<string, GeoJson> {
  const out: Record<string, GeoJson> = {};
  if (!geojson) return out;
  for (const f of geojson.features) {
    const key = String((f.properties as Record<string, unknown>)[prop] || "other");
    if (!out[key]) out[key] = { type: "FeatureCollection", features: [] };
    out[key].features.push(f);
  }
  return out;
}

function addFeaturesProp(geojson: GeoJson | null, fn: (f: GeoJsonFeature) => Record<string, unknown>): GeoJson | null {
  if (!geojson) return null;
  return { type: "FeatureCollection", features: geojson.features.map((f) => ({ ...f, properties: { ...f.properties, ...fn(f) } })) };
}

export function MapView({ hotspots, selectedId, onSelect, focus, className }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const selectedRef = useRef(selectedId);
  selectedRef.current = selectedId;

  const [basemap, setBasemap] = useState<"light" | "satellite">("light");
  const [visible, setVisible] = useState<Record<LayerId, boolean>>(DEFAULT_VISIBLE);
  const [ready, setReady] = useState(false);
  const [infra, setInfra] = useState<GeoJson | null>(null);
  const [zones, setZones] = useState<GeoJson | null>(null);
  const [landcover, setLandcover] = useState<GeoJson | null>(null);
  const [network, setNetwork] = useState<GeoJson | null>(null);

  useEffect(() => {
    getInfrastructureGeojson().then(setInfra).catch(() => setInfra(null));
    getZonesGeojson().then(setZones).catch(() => setZones(null));
    getLandcoverGeojson().then(setLandcover).catch(() => setLandcover(null));
    getNetworkGeojson().then(setNetwork).catch(() => setNetwork(null));
  }, []);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    setReady(false);
    const el = containerRef.current;
    const map = new maplibregl.Map({
      container: el,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          basemap: { type: "raster", tiles: [LIGHT_TILES], tileSize: 256, attribution: "© CARTO © OpenStreetMap" },
          satellite: { type: "raster", tiles: [SATELLITE_TILES], tileSize: 256, attribution: "© Esri" },
        },
        layers: [
          { id: "satellite-layer", type: "raster", source: "satellite", layout: { visibility: "none" } },
          { id: "basemap-layer", type: "raster", source: "basemap" },
        ],
      },
      center: [78.96, 22.35],
      zoom: 4.6,
      maxBounds: [[60, 2], [104, 40]] as [[number, number], [number, number]],
      attributionControl: { compact: true },
    });
    
    mapRef.current = map;
    
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(el);

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-left");
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-left");
    map.on("load", () => {
      setReady(true);
      map.fitBounds(INDIA_BOUNDS, { padding: 24, duration: 0 });
    });

    // Query with a small padded bbox so small dots and touch taps register.
    const HOTSPOT_HIT_LAYERS = ["hotspot-circle", "hotspot-cluster"];
    const pickHotspot = (point: { x: number; y: number }) => {
      const layers = HOTSPOT_HIT_LAYERS.filter((l) => map.getLayer(l));
      if (!layers.length) return [];
      const bbox: [[number, number], [number, number]] = [
        [point.x - 8, point.y - 8],
        [point.x + 8, point.y + 8],
      ];
      return map.queryRenderedFeatures(bbox, { layers });
    };

    map.on("click", (e) => {
      const feats = pickHotspot(e.point);
      const f = feats[0];
      if (!f) return;
      const p = f.properties as Record<string, unknown>;
      const coords = (f.geometry as unknown as { coordinates: [number, number] }).coordinates;

      if (p.point_count) {
        // Cluster: expand it so individual hotspots become visible.
        const source = map.getSource("hotspots") as maplibregl.GeoJSONSource | undefined;
        if (!source) return;
        source
          .getClusterExpansionZoom(Number(p.cluster_id))
          .then((zoom) => map.easeTo({ center: coords, zoom: Math.min(zoom + 0.2, 14), duration: 600 }))
          .catch(() => undefined);
        return;
      }

      if (onSelect) onSelect(Number(p.id), String(p.code));
      // Nudge the camera so the selected dot sits left of the detail panel.
      map.easeTo({
        center: coords,
        zoom: Math.max(map.getZoom(), 8),
        offset: window.innerWidth >= 1024 ? [-150, 0] : [0, 0],
        duration: 600,
      });
    });
    HOTSPOT_HIT_LAYERS.forEach((layer) => {
      map.on("mouseenter", layer, () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", layer, () => (map.getCanvas().style.cursor = ""));
    });

    let popup: maplibregl.Popup | null = null;
    map.on("mousemove", (e) => {
      const feats = pickHotspot(e.point);
      if (!feats.length) {
        popup?.remove();
        popup = null;
        return;
      }
      const p = feats[0].properties as Record<string, unknown>;
      // Colors reference theme CSS variables so the popup works in light and dark mode.
      const html = p.point_count
        ? `<div style="min-width:150px;color:rgb(var(--rgb-primary))">
            <div style="font-weight:700">${p.point_count} hotspots</div>
            <div style="color:rgb(var(--rgb-muted));font-size:11px">Click to zoom in and expand</div>
          </div>`
        : `<div style="min-width:170px;color:rgb(var(--rgb-primary))">
            <div style="font-weight:700">${escapeHtml(p.code)}</div>
            <div style="font-weight:600;color:${RISK_COLORS[String(p.risk_level)] || "rgb(var(--rgb-muted))"}">${escapeHtml(p.risk_level)} · risk ${Math.round(Number(p.risk_score ?? 0))}/100</div>
            <div style="color:rgb(var(--rgb-secondary));font-size:11px">${escapeHtml(p.classification)}</div>
            <div style="color:rgb(var(--rgb-muted));font-size:11px">FRP ${Number(p.frp ?? 0).toFixed(1)} MW · ${escapeHtml(p.state)}</div>
          </div>`;
      if (!popup) popup = new maplibregl.Popup({ closeButton: false, offset: 12, maxWidth: "240px" }).addTo(map);
      popup.setLngLat(e.lngLat).setHTML(html);
    });
    return () => {
      ro.disconnect();
      popup?.remove();
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setLayoutProperty("basemap-layer", "visibility", basemap === "light" ? "visible" : "none");
    map.setLayoutProperty("satellite-layer", "visibility", basemap === "satellite" ? "visible" : "none");
  }, [basemap, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !focus) return;
    map.flyTo({ center: [focus.lon, focus.lat], zoom: focus.zoom ?? 9, essential: true, duration: 1600 });
  }, [focus?.key, focus?.lat, focus?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  // Hotspot layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !hotspots) return;
    ensureHotspotLayers(map, hotspots);
  }, [hotspots, ready]);

  // Zone layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !zones) return;
    const styled = addFeaturesProp(zones, (f) => ({
      color: RISK_COLORS[String(f.properties.risk_level)] || "#64748b",
      radius: Math.max(5, Number(f.properties.radius_km) || 6),
    }));
    ensurePointLayers(map, "zone", styled, (f) => Number(f.properties.radius) * 1.4);
  }, [zones, ready]);

  // Infra layers by type
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !infra) return;
    const byType = splitByProp(infra, "infra_type");
    (Object.keys(INFRA_STYLE) as (keyof typeof INFRA_STYLE)[]).forEach((type) => {
      const fc = byType[type];
      if (!fc) return;
      const styled = addFeaturesProp(fc, () => ({ ...INFRA_STYLE[type], name: fc.features[0]?.properties?.name || "" }));
      ensurePointLayers(map, `infra-${type}`, styled, (f) => (f.properties as Record<string, unknown>).radius as number);
    });
  }, [infra, ready]);

  // Landcover polygons
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !landcover) return;
    const byLayer = splitByProp(landcover, "layer");
    (Object.keys(LANDCOVER_STYLE) as (keyof typeof LANDCOVER_STYLE)[]).forEach((layer) => {
      const fc = byLayer[layer];
      if (!fc) return;
      const styled = addFeaturesProp(fc, () => LANDCOVER_STYLE[layer]);
      ensurePolygonLayers(map, `landcover-${layer}`, styled);
    });
  }, [landcover, ready]);

  // Network lines
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !network) return;
    const byLayer = splitByProp(network, "layer");
    (Object.keys(NETWORK_STYLE) as (keyof typeof NETWORK_STYLE)[]).forEach((layer) => {
      const fc = byLayer[layer];
      if (!fc) return;
      const styled = addFeaturesProp(fc, () => NETWORK_STYLE[layer]);
      ensureLineLayers(map, `network-${layer}`, styled);
    });
  }, [network, ready]);

  // Visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (Object.keys(VISIBILITY_MAP) as LayerId[]).forEach((id) => {
      VISIBILITY_MAP[id].forEach((lid) => {
        if (map.getLayer(lid)) map.setLayoutProperty(lid, "visibility", visible[id] ? "visible" : "none");
      });
    });
  }, [visible, ready, infra, zones, landcover, network, hotspots]);

  // Selected highlight
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !map.getLayer("hotspot-circle")) return;
    try {
      map.setPaintProperty("hotspot-circle", "circle-stroke-color", [
        "case", ["==", ["get", "id"], selectedRef.current ?? -1], "#ffffff", "rgba(0,0,0,0)",
      ]);
      map.setPaintProperty("hotspot-circle", "circle-stroke-width", ["case", ["==", ["get", "id"], selectedRef.current ?? -1], 2.5, 0]);
    } catch {
      /* ignore */
    }
  }, [selectedId, ready]);

  return (
    <div className={cn("relative h-full w-full overflow-hidden", className)}>
      <div ref={containerRef} className="absolute inset-0" role="application" aria-label="Fire hotspot map" />
      {ready && (
        <>
          <LayerControl visible={visible} onChange={setVisible} basemap={basemap} onBasemap={setBasemap} />
          <MapLegend visible={visible} />
        </>
      )}
    </div>
  );
}

// ---------------- layer builders ----------------

function ensureHotspotLayers(map: maplibregl.Map, geojson: GeoJson) {
  const gj = geojson as unknown as maplibregl.GeoJSONSourceSpecification["data"];
  if (!map.getSource("hotspots")) {
    map.addSource("hotspots", { type: "geojson", data: gj, cluster: true, clusterMaxZoom: 7, clusterRadius: 48 });
  } else {
    (map.getSource("hotspots") as maplibregl.GeoJSONSource).setData(gj);
  }
  if (!map.getLayer("risk-heat")) {
    map.addLayer({
      id: "risk-heat",
      type: "heatmap",
      source: "hotspots",
      layout: { visibility: "none" },
      paint: {
        "heatmap-weight": ["interpolate", ["linear"], ["get", "risk_score"], 0, 0, 100, 1],
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 0.6, 8, 2.2],
        "heatmap-color": [
          "interpolate", ["linear"], ["heatmap-density"],
          0, "rgba(34,197,94,0)",
          0.25, "rgba(59,130,246,0.35)",
          0.5, "rgba(234,179,8,0.5)",
          0.75, "rgba(249,115,22,0.65)",
          1, "rgba(239,68,68,0.85)",
        ],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 16, 8, 42],
        "heatmap-opacity": 0.55,
      },
    });
  }
  if (!map.getLayer("hotspot-cluster")) {
    map.addLayer({
      id: "hotspot-cluster",
      type: "circle",
      source: "hotspots",
      filter: ["has", "point_count"],
      paint: {
        "circle-color": ["step", ["get", "point_count"], "#3b82f6", 10, "#eab308", 30, "#ef4444"],
        "circle-radius": ["step", ["get", "point_count"], 14, 10, 19, 30, 25],
        "circle-opacity": 0.75,
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "rgba(255,255,255,0.35)",
      },
    });
  }
  if (!map.getLayer("hotspot-circle")) {
    map.addLayer({
      id: "hotspot-circle",
      type: "circle",
      source: "hotspots",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-radius": [
          "interpolate", ["linear"], ["zoom"],
          0, ["interpolate", ["linear"], ["get", "risk_score"], 0, 5, 100, 9],
          8, ["interpolate", ["linear"], ["get", "risk_score"], 0, 7, 100, 14],
        ],
        "circle-color": ["match", ["get", "risk_level"], "CRITICAL", "#ef4444", "HIGH", "#f97316", "ELEVATED", "#eab308", "MODERATE", "#3b82f6", "LOW", "#22c55e", "#64748b"],
        "circle-opacity": 0.9,
        "circle-blur": 0.25,
        "circle-stroke-width": 1,
        "circle-stroke-color": "rgba(255,255,255,0.5)",
      },
    });
  }
}

function ensurePointLayers(map: maplibregl.Map, id: string, geojson: GeoJson | null, radiusFn: (f: GeoJsonFeature) => number) {
  if (!geojson) return;
  const gj = geojson as unknown as maplibregl.GeoJSONSourceSpecification["data"];
  if (!map.getSource(id)) map.addSource(id, { type: "geojson", data: gj });
  else (map.getSource(id) as maplibregl.GeoJSONSource).setData(gj);
  if (!map.getLayer(`${id}-fill`)) {
    map.addLayer({
      id: `${id}-fill`,
      type: "circle",
      source: id,
      paint: {
        "circle-radius": ["get", "radius"],
        "circle-color": ["get", "color"],
        "circle-opacity": 0.5,
        "circle-stroke-width": 1,
        "circle-stroke-color": ["get", "color"],
      },
    });
  }
}

function ensurePolygonLayers(map: maplibregl.Map, id: string, geojson: GeoJson | null) {
  if (!geojson) return;
  const gj = geojson as unknown as maplibregl.GeoJSONSourceSpecification["data"];
  if (!map.getSource(id)) map.addSource(id, { type: "geojson", data: gj });
  else (map.getSource(id) as maplibregl.GeoJSONSource).setData(gj);
  if (!map.getLayer(`${id}-fill`)) {
    map.addLayer({
      id: `${id}-fill`,
      type: "fill",
      source: id,
      paint: { "fill-color": ["get", "color"], "fill-opacity": ["get", "opacity"] },
    });
    map.addLayer({
      id: `${id}-line`,
      type: "line",
      source: id,
      paint: { "line-color": ["get", "color"], "line-width": 0.8, "line-opacity": 0.55 },
    });
  }
}

function ensureLineLayers(map: maplibregl.Map, id: string, geojson: GeoJson | null) {
  if (!geojson) return;
  const gj = geojson as unknown as maplibregl.GeoJSONSourceSpecification["data"];
  if (!map.getSource(id)) map.addSource(id, { type: "geojson", data: gj });
  else (map.getSource(id) as maplibregl.GeoJSONSource).setData(gj);
  if (!map.getLayer(id)) {
    map.addLayer({
      id,
      type: "line",
      source: id,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": ["get", "color"],
        "line-width": ["get", "width"],
        "line-opacity": ["get", "opacity"],
      },
    });
  }
}