"use client";

import { cn } from "@/lib/utils";

function colorFor(value: number) {
  if (value >= 81) return "#ef4444";
  if (value >= 61) return "#f97316";
  if (value >= 41) return "#eab308";
  if (value >= 21) return "#3b82f6";
  return "#22c55e";
}

export function RiskGauge({ score, level, size = 150 }: { score: number; level: string; size?: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const angle = (pct / 100) * 180;
  const color = colorFor(pct);
  // SVG semicircle arc
  const r = 60;
  const cx = 75;
  const cy = 70;
  const largeArc = angle > 90 ? 1 : 0;
  const endX = cx + r * Math.cos(Math.PI - (angle * Math.PI) / 180);
  const endY = cy - r * Math.sin((angle * Math.PI) / 180);
  const arc = angle <= 0 ? "" : `M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${endX} ${endY}`;

  return (
    <div className="flex flex-col items-center" role="img" aria-label={`Risk ${score} out of 100, level ${level}`}>
      <svg width={size} height={size * 0.55} viewBox="0 0 150 75">
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 1 1 ${cx + r} ${cy}`} fill="none" stroke="#1e293b" strokeWidth="10" strokeLinecap="round" />
        {arc && <path d={arc} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round" />}
      </svg>
      <div className="-mt-2 text-center">
        <span className="font-mono text-2xl font-bold" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="text-xs text-slate-500"> / 100</span>
        <div className="text-[11px] font-semibold tracking-widest" style={{ color }}>
          {level}
        </div>
      </div>
    </div>
  );
}

export function ConfidenceGauge({ value, label = "Confidence" }: { value: number; label?: string }) {
  const pct = Math.max(0, Math.min(100, value * 100));
  const color = pct >= 80 ? "#22c55e" : pct >= 60 ? "#eab308" : "#f97316";
  return (
    <div className="w-full" role="img" aria-label={`${label} ${pct} percent`}>
      <div className="mb-1 flex items-center justify-between text-[11px]">
        <span className="text-slate-600">{label}</span>
        <span className="font-mono font-semibold" style={{ color }}>
          {Math.round(pct)}%
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export function TrendSparkline({ values, className }: { values: number[]; className?: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const w = 80;
  const h = 24;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - ((v - min) / range) * (h - 4) - 2}`).join(" ");
  const up = values[values.length - 1] >= values[0];
  const color = up ? "#22c55e" : "#ef4444";
  return (
    <svg width={w} height={h} className={cn("inline-block", className)} aria-hidden>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}