"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { Card } from "@/components/ui/primitives";
import { TrendSparkline } from "@/components/gauges";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  change,
  icon,
  tone = "info",
  spark,
  sub,
}: {
  label: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  tone?: "critical" | "high" | "moderate" | "low" | "info";
  spark?: number[];
  sub?: string;
}) {
  const toneText: Record<string, string> = {
    critical: "text-critical",
    high: "text-high",
    moderate: "text-moderate",
    low: "text-low",
    info: "text-accent",
  };
  const toneBorder: Record<string, string> = {
    critical: "border-t-critical/70",
    high: "border-t-high/70",
    moderate: "border-t-moderate/70",
    low: "border-t-low/70",
    info: "border-t-accent/70",
  };
  const toneBg: Record<string, string> = {
    critical: "bg-critical",
    high: "bg-high",
    moderate: "bg-moderate",
    low: "bg-low",
    info: "bg-accent",
  };
  const positive = (change ?? 0) >= 0;
  return (
    <Card className={cn("border-t-2 px-4 py-3", toneBorder[tone])}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-wider text-muted">{label}</p>
          <p className={cn("mt-1 font-mono text-2xl font-bold", toneText[tone])}>{value}</p>
          <div className="mt-1 flex items-center gap-2">
            {change !== undefined && (
              <span className={cn("inline-flex items-center gap-0.5 text-[11px] font-medium", positive ? "text-low" : "text-critical")}>
                {change === 0 ? <Minus className="h-3 w-3" /> : positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                {Math.abs(change).toFixed(1)}%
              </span>
            )}
            {sub && <span className="text-[10px] text-muted">{sub}</span>}
            {spark && <TrendSparkline values={spark} />}
          </div>
        </div>
        {icon && <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white", toneBg[tone])}>{icon}</div>}
      </div>
    </Card>
  );
}