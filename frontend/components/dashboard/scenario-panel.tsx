"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, ChevronRight, Loader2, Play, Radio } from "lucide-react";
import { runDemoScenario, getScenarioState } from "@/lib/api";
import type { ScenarioResult } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, CardTitle, Dialog, useToast } from "@/components/ui/primitives";
import { RiskBadge } from "@/components/badges";
import { cn } from "@/lib/utils";

export function ScenarioPanel({
  onStep,
  onDone,
  onRestore,
}: {
  onStep?: (phase: number, result: ScenarioResult) => void;
  onDone?: (result: ScenarioResult) => void;
  onRestore?: (result: ScenarioResult) => void;
}) {
  const [running, setRunning] = useState(false);
  const [open, setOpen] = useState(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [phase, setPhase] = useState(0);
  const { push } = useToast();

  const run = async () => {
    setRunning(true);
    setOpen(true);
    setVisibleSteps(0);
    setPhase(0);
    try {
      const res = await runDemoScenario();
      setResult(res);
      // Animate step progression
      res.steps.forEach((_, i) => {
        setTimeout(() => {
          setVisibleSteps(i + 1);
          setPhase(i + 1);
          onStep?.(i + 1, res);
        }, (i + 1) * 1300);
      });
      setTimeout(() => {
        onDone?.(res);
        push({ title: "Scenario complete", message: "Industrial fire escalated to CRITICAL. Alert generated.", tone: "critical" });
      }, (res.steps.length + 1) * 1300);
    } catch (e) {
      push({ title: "Scenario failed", message: e instanceof Error ? e.message : "Could not run scenario", tone: "error" });
      setOpen(false);
    } finally {
      setRunning(false);
    }
  };

  const restore = async () => {
    try {
      const state = await getScenarioState();
      if (state.hotspot && state.zone && state.alert) {
        const fake = {
          scenario: "Industrial Fire Escalation Scenario",
          completed: true,
          persistent_hotspot: state.hotspot,
          hotspot: state.hotspot,
          alert: state.alert,
          zone: state.zone,
          risk_trend: [62, 71, 78, state.hotspot.risk_score],
          steps: [
            { phase: 1, title: "Persistent thermal source detected", detail: "Seeded detection history restored.", risk_score: 55, classification: "Persistent Industrial Heat Source" },
            { phase: 2, title: "Sudden high-intensity detection", detail: "Escalation hotspot restored.", risk_score: 70, classification: "Industrial Fire" },
            { phase: 3, title: "Satellite validation indicates smoke", detail: "Validation status CONFIRMED.", risk_score: 78, classification: "Industrial Fire" },
            { phase: 4, title: "Classification escalated to Industrial Fire", detail: "Alert generated.", risk_score: state.hotspot.risk_score, classification: "Industrial Fire" },
            { phase: 5, title: `${state.zone.name} zone set to CRITICAL`, detail: "Monitoring INTENSIVE.", risk_score: state.hotspot.risk_score, classification: "Industrial Fire" },
          ],
        } as ScenarioResult;
        setResult(fake);
        setOpen(true);
        setVisibleSteps(5);
        setPhase(5);
        onRestore?.(fake);
        push({ title: "Scenario restored", message: "Previous scenario state loaded.", tone: "info" });
      } else {
        push({ title: "No scenario yet", message: "Run the scenario first to create escalation state.", tone: "info" });
      }
    } catch {
      push({ title: "Restore failed", message: "Backend unavailable.", tone: "error" });
    }
  };

  return (
    <Card className="scan-overlay relative overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-accent" /> Demo Scenario
        </CardTitle>
      </CardHeader>
      <CardBody>
        <p className="text-xs font-semibold text-primary">Industrial Fire Escalation Scenario</p>
        <p className="mt-1 text-[11px] leading-relaxed text-muted">
          Persistent heat source near a refinery escalates into a CRITICAL industrial fire: classification flips, risk climbs to 87/100, an alert is auto-generated and the zone goes CRITICAL.
        </p>
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={run} disabled={running}>
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            Run Demo Scenario
          </Button>
          <Button variant="outline" size="sm" onClick={restore}>
            Restore last run
          </Button>
        </div>
      </CardBody>

      <Dialog open={open} onClose={() => setOpen(false)} title="Industrial Fire Escalation Scenario" wide>
        {result && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs text-muted">Live classification:</span>
              <Badge tone="critical">{phase >= 4 ? "Industrial Fire" : phase >= 1 ? "Persistent Industrial Heat Source" : "Running..."}</Badge>
              <span className="text-xs text-muted">Risk:</span>
              <RiskBadge level={phase >= 4 ? "CRITICAL" : phase >= 2 ? "HIGH" : "MODERATE"} score={result.risk_trend[Math.min(phase, 3)]} />
            </div>

            <ol className="space-y-2">
              {result.steps.map((s, i) => {
                const shown = i < visibleSteps;
                const active = i === visibleSteps - 1;
                return (
                  <li
                    key={s.phase}
                    className={cn(
                      "rounded-md border px-3 py-2 transition-all",
                      active ? "border-accent/60 bg-sky-600/10" : shown ? "border-base-border/60 bg-base-raised/40" : "border-base-border/30 opacity-40"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {shown ? <CheckCircle2 className="h-3.5 w-3.5 text-low" /> : <ChevronRight className="h-3.5 w-3.5 text-muted" />}
                      <span className={cn("text-xs font-semibold", shown ? "text-primary" : "text-muted")}>
                        Phase {s.phase}: {s.title}
                      </span>
                      {shown && <span className="ml-auto font-mono text-[10px] text-muted">risk {Math.round(s.risk_score)}</span>}
                    </div>
                    {shown && <p className="mt-1 pl-5 text-[11px] text-muted">{s.detail}</p>}
                  </li>
                );
              })}
            </ol>

            {visibleSteps >= 5 && (
              <div className="flex flex-wrap items-center gap-3 rounded-md border border-critical/40 bg-critical/5 px-3 py-2.5">
                <span className="text-xs font-semibold text-critical">CRITICAL ALERT GENERATED</span>
                <span className="text-xs text-secondary">{result.alert.code}</span>
                <span className="ml-auto flex gap-2">
                  <Link href={`/hotspots/${result.hotspot.id}`}>
                    <Button size="sm" variant="outline">View hotspot</Button>
                  </Link>
                  <Link href="/alerts">
                    <Button size="sm">Open alert center</Button>
                  </Link>
                </span>
              </div>
            )}
          </div>
        )}
      </Dialog>
    </Card>
  );
}