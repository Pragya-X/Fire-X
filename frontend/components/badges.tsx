"use client";

import { AlertTriangle, Circle, Flame, Mountain, Sprout, Star, Thermometer } from "lucide-react";
import { Badge, type BadgeTone } from "@/components/ui/primitives";

const RISK_TONE: Record<string, BadgeTone> = {
  CRITICAL: "critical",
  HIGH: "high",
  ELEVATED: "moderate",
  MODERATE: "info",
  LOW: "low",
};

export function RiskBadge({ level, score, showScore = true }: { level: string; score?: number; showScore?: boolean }) {
  return (
    <Badge tone={RISK_TONE[level] || "muted"} icon={level === "CRITICAL" ? <AlertTriangle className="h-3 w-3" /> : undefined}>
      {showScore && score !== undefined ? `${Math.round(score)} ` : ""}
      {level}
    </Badge>
  );
}

const CLASS_ICON: Record<string, React.ReactNode> = {
  "Industrial Fire": <Flame className="h-3 w-3" />,
  "Persistent Industrial Heat Source": <Thermometer className="h-3 w-3" />,
  "Gas Flare": <Star className="h-3 w-3" />,
  Wildfire: <Mountain className="h-3 w-3" />,
  "Agricultural Burning": <Sprout className="h-3 w-3" />,
  "Other Thermal Anomaly": <Circle className="h-3 w-3" />,
};

export function ClassificationBadge({ classification, confidence }: { classification: string; confidence?: number }) {
  const tone: BadgeTone =
    classification === "Industrial Fire"
      ? "critical"
      : classification === "Wildfire"
        ? "high"
        : classification === "Agricultural Burning"
          ? "moderate"
          : classification === "Gas Flare"
            ? "purple"
            : classification === "Persistent Industrial Heat Source"
              ? "info"
              : "muted";
  return (
    <Badge tone={tone} icon={CLASS_ICON[classification]}>
      {classification}
      {confidence !== undefined && ` · ${Math.round(confidence * 100)}%`}
    </Badge>
  );
}
