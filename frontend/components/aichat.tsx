"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bot, Loader2, Send, Sparkles, User } from "lucide-react";
import { askCopilot, getCopilotSuggestions } from "@/lib/api";
import { Badge, Button, Textarea, useToast } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  text: string;
  mode?: string;
  links?: { label: string; href: string }[];
}

export function AIChat() {
  const { push } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getCopilotSuggestions().then((r) => setSuggestions(r.items)).catch(() => undefined);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setBusy(true);
    try {
      const res = await askCopilot(q);
      const links: Message["links"] = [];
      if (res.data?.hotspots && Array.isArray(res.data.hotspots) && (res.data.hotspots as { id?: number }[])[0]?.id) {
        links.push({ label: "Open hotspot", href: `/hotspots/${(res.data.hotspots as { id: number }[])[0].id}` });
      }
      if (res.data?.zones && Array.isArray(res.data.zones) && (res.data.zones as { id?: number }[])[0]?.id) {
        links.push({ label: "Open zone", href: `/industrial-zones?zone=${(res.data.zones as { id: number }[])[0].id}` });
      }
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer, mode: res.mode, links }]);
    } catch (e) {
      push({ title: "Copilot error", message: e instanceof Error ? e.message : "Backend unavailable", tone: "error" });
      setMessages((prev) => [...prev, { role: "assistant", text: "I could not reach the FIRE-X backend. Check that the API is running and try again." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-base-border/70 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md border border-accent/40 bg-base-raised">
            <Bot className="h-4 w-4 text-accent" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">FIRE-X Copilot</p>
            <p className="text-[10px] text-slate-500">Answers from live application data</p>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="rounded-lg border border-base-border/60 bg-base-raised/40 p-3 text-xs leading-relaxed text-slate-600">
              Ask me anything about the fire situation. I query the FIRE-X APIs directly - I never invent facts. Example questions:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {suggestions.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-full border border-base-border bg-base-raised/50 px-3 py-1.5 text-[11px] text-slate-700 transition-colors hover:border-accent/50 hover:text-slate-900">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={cn("flex gap-2.5", m.role === "user" ? "justify-end" : "justify-start")}>
            {m.role === "assistant" && (
              <span className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-accent/40 bg-base-raised">
                <Bot className="h-3 w-3 text-accent" />
              </span>
            )}
            <div className={cn("max-w-[85%] rounded-lg border px-3 py-2", m.role === "user" ? "border-sky-600/40 bg-sky-600/15" : "border-base-border bg-base-raised/60")}>
              <div className="flex items-center gap-2">
                {m.role === "user" ? (
                  <User className="h-3 w-3 text-slate-600" />
                ) : (
                  <Sparkles className="h-3 w-3 text-accent" />
                )}
                <span className="text-[9px] uppercase tracking-wider text-slate-500">{m.role === "user" ? "You" : "Copilot"}{m.mode === "llm" ? " · LLM" : ""}</span>
              </div>
              <p className="mt-1 whitespace-pre-wrap text-xs leading-relaxed text-slate-900">{m.text}</p>
              {m.links && m.links.length > 0 && (
                <div className="mt-2 flex gap-2">
                  {m.links.map((l) => (
                    <Link key={l.href} href={l.href} className="rounded border border-accent/40 bg-sky-600/10 px-2 py-1 text-[10px] text-accent hover:bg-sky-600/20">
                      {l.label} →
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Querying data...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-base-border/70 p-3">
        <div className="flex items-end gap-2">
          <Textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Ask about hotspots, zones, risk, incidents..."
            className="max-h-28 min-h-[38px]"
            aria-label="Ask FIRE-X Copilot"
          />
          <Button onClick={() => send()} disabled={busy || !input.trim()} aria-label="Send question">
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="mt-1.5 text-[9px] text-slate-600">
          Answers are built from backend queries over application data. Configure OPENAI_API_KEY for LLM responses grounded in the same data.
        </p>
      </div>
    </div>
  );
}