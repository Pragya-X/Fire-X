import { getHotspots, getIndustrialZones } from "@/lib/api";

export interface SearchResult {
  label: string;
  href: string;
  meta: string;
}

/** Search hotspots and industrial zones for direct navigation. */
export async function searchHotspots(q: string): Promise<SearchResult[]> {
  const out: SearchResult[] = [];
  const term = q.trim();
  const isCode = /^HX-\d{3,4}$/i.test(term);

  if (isCode) {
    const res = await getHotspots({ search: term, page_size: 10 });
    for (const h of res.items) {
      out.push({
        label: `${h.code} - ${h.classification} (${h.risk_level})`,
        href: `/hotspots/${h.id}`,
        meta: `${h.state} / ${h.district}`,
      });
    }
    return out;
  }

  const res = await getHotspots({ search: term, page_size: 8 });
  for (const h of res.items) {
    out.push({
      label: `${h.code} - ${h.classification}`,
      href: `/hotspots/${h.id}`,
      meta: `${h.state} / ${h.district} · ${h.risk_level}`,
    });
  }

  const zones = await getIndustrialZones();
  for (const z of zones.items) {
    if (z.name.toLowerCase().includes(term.toLowerCase()) || z.state.toLowerCase().includes(term.toLowerCase()) || z.district.toLowerCase().includes(term.toLowerCase())) {
      out.push({
        label: `${z.name} (${z.zone_type})`,
        href: `/industrial-zones?zone=${z.id}`,
        meta: `${z.state} · ${z.risk_level}`,
      });
    }
  }

  // State-level search: list hotspots in that state
  const stateMatch = await getHotspots({ state: term, page_size: 3 }).catch(() => null);
  if (stateMatch && stateMatch.total > 0 && out.length < 8) {
    out.push({
      label: `${stateMatch.total} hotspots in ${term}`,
      href: `/hotspots?state=${encodeURIComponent(term)}`,
      meta: "state filter",
    });
  }

  return out.slice(0, 12);
}
