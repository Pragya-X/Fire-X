"use client";

import { useEffect, useRef, useState } from "react";
import type { SatelliteValidation } from "@/lib/types";

/**
 * Demo satellite imagery renderer.
 * Draws a synthetic before/after scene from validation parameters (NDVI,
 * burn area, smoke) onto a canvas. Clearly labeled "Demo Satellite Layer" -
 * it never claims to be live imagery.
 */
export function SatelliteComparison({ validation, label = "Demo Satellite Layer" }: { validation: SatelliteValidation | null; label?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [slider, setSlider] = useState(50);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const W = canvas.width;
    const H = canvas.height;

    ctx.clearRect(0, 0, W, H);

    if (!validation) {
      ctx.fillStyle = "#0a101c";
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = "#475569";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Select a hotspot to render satellite imagery", W / 2, H / 2);
      return;
    }

    const draw = (before: boolean) => {
      ctx.clearRect(0, 0, W, H);
      // ground texture
      const rng = mulberry32(validation.id * 7 + (before ? 1 : 2));
      for (let y = 0; y < H; y += 4) {
        for (let x = 0; x < W; x += 4) {
          const n = rng();
          const ndvi = (before ? validation.ndvi_before : validation.ndvi_after) ?? 0;
          let r = 40, g = 60, b = 35;
          if (n > 0.75) { r = 70 + n * 40; g = 80; b = 45; } // soil
          else { r = 30 + ndvi * 120; g = 60 + ndvi * 160; b = 30 + ndvi * 40; } // vegetation
          ctx.fillStyle = `rgb(${Math.min(255, r)},${Math.min(255, g)},${Math.min(255, b)})`;
          ctx.fillRect(x, y, 4, 4);
        }
      }

      if (!before) {
        // burn scar
        const burnW = Math.min(W * 0.35, (validation.burn_area_ha ?? 0) * 6);
        const burnH = Math.min(H * 0.28, (validation.fire_extent_km2 ?? 0) * 40 + 20);
        const bx = W * 0.45 - burnW / 2;
        const by = H * 0.5 - burnH / 2;
        ctx.fillStyle = "rgba(30,20,15,0.9)";
        ctx.beginPath();
        ctx.ellipse(W * 0.45, H * 0.5, burnW / 2, burnH / 2, 0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "rgba(60,35,20,0.8)";
        ctx.beginPath();
        ctx.ellipse(W * 0.45, H * 0.5, burnW / 3, burnH / 3, -0.1, 0, Math.PI * 2);
        ctx.fill();
      }

      if (validation.smoke_indication && !before) {
        // smoke plume
        ctx.fillStyle = "rgba(200,205,215,0.35)";
        for (let i = 0; i < 6; i++) {
          ctx.beginPath();
          ctx.arc(W * 0.45 + i * 14 - 40, H * 0.32 - i * 10, 14 + i * 3, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // infrastructure grid (roads/plots)
      ctx.strokeStyle = "rgba(255,255,255,0.14)";
      ctx.lineWidth = 1;
      for (let i = 1; i < 6; i++) {
        ctx.beginPath(); ctx.moveTo((W / 6) * i, 0); ctx.lineTo((W / 6) * i, H); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, (H / 6) * i); ctx.lineTo(W, (H / 6) * i); ctx.stroke();
      }
    };

    draw(slider < 50);
    // Reveal overlay based on slider
    const reveal = Math.abs(slider - 50) * 2;
    const x = (slider / 100) * W;
    ctx.fillStyle = "rgba(0,0,0,0.35)";
    ctx.fillRect(x, 0, W - x, H);
  }, [validation, slider]);

  if (!validation) return <div className="rounded-lg border border-base-border p-6 text-sm text-muted">Select a hotspot to render satellite imagery</div>;

  // For live providers (planet, etc.), show the synthetic demo scene
  // as the best available before/after representation, clearly labeled.
  const isLive = validation.provider !== "demo";
  const displayLabel = isLive ? `${label} (Live: ${validation.provider})` : label;

  return (
    <div className="w-full">
      <div className="relative overflow-hidden rounded-lg border border-base-border">
        <canvas ref={canvasRef} width={640} height={360} className="block h-auto w-full" aria-label={`${label}: before/after comparison`} />
        <span className="absolute left-2 top-2 rounded bg-slate-900/70 px-2 py-0.5 text-[10px] font-semibold text-white">BEFORE</span>
        <span className="absolute right-2 top-2 rounded bg-slate-900/70 px-2 py-0.5 text-[10px] font-semibold text-white">AFTER</span>
        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded bg-slate-900/70 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest text-white">{displayLabel}</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={slider}
        onChange={(e) => setSlider(Number(e.target.value))}
        className="mt-3 w-full accent-sky-500"
        aria-label="Before/after comparison slider"
      />
      <div className="flex justify-between text-[10px] text-muted">
        <span>Before (NDVI {validation?.ndvi_before ?? "-"})</span>
        <span>After (NDVI {validation?.ndvi_after ?? "-"})</span>
      </div>
    </div>
  );
}

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}