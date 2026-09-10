"use client";

import { Card } from "@/components/ui/primitives";
import { AIChat } from "@/components/aichat";

export default function CopilotPage() {
  return (
    <div className="flex h-full flex-col space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-700 tracking-tight">AI Copilot</h1>
        <p className="text-xs text-slate-400 mt-0.5">Enterprise analyst assistant · evidence-backed responses · database-verified answers</p>
      </div>
      <Card className="min-h-0 flex-1 overflow-hidden">
        <div className="h-[calc(100vh-200px)]">
          <AIChat />
        </div>
      </Card>
    </div>
  );
}