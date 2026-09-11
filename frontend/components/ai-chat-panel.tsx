"use client";

import { useEffect, useRef, useState } from "react";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { Bot, Loader2, Send, Sparkles, X, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "model";
  text: string;
}

/* ------------------------- Minimal markdown rendering ------------------------- */

function renderInline(text: string, keyPrefix: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) {
      return <strong key={`${keyPrefix}-${i}`} className="font-semibold text-primary">{part.slice(2, -2)}</strong>;
    }
    if (/^\*[^*]+\*$/.test(part)) {
      return <em key={`${keyPrefix}-${i}`}>{part.slice(1, -1)}</em>;
    }
    if (/^`[^`]+`$/.test(part)) {
      return <code key={`${keyPrefix}-${i}`} className="rounded bg-base px-1 py-0.5 font-mono text-[12px]">{part.slice(1, -1)}</code>;
    }
    return <span key={`${keyPrefix}-${i}`}>{part}</span>;
  });
}

function MarkdownMessage({ text }: { text: string }) {
  const blocks: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = (key: string) => {
    if (listItems.length > 0) {
      blocks.push(
        <ul key={key} className="ml-4 list-disc space-y-1">
          {listItems.map((item, i) => (
            <li key={i}>{renderInline(item, `${key}-${i}`)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  text.split("\n").forEach((line, idx) => {
    const bullet = /^\s*[*\-•]\s+(.*)$/.exec(line);
    const heading = /^\s*#{1,6}\s+(.*)$/.exec(line);

    if (bullet) {
      listItems.push(bullet[1]);
      return;
    }
    flushList(`ul-${idx}`);
    if (heading) {
      blocks.push(<p key={idx} className="font-semibold text-primary">{renderInline(heading[1], `h-${idx}`)}</p>);
      return;
    }
    if (line.trim() === "") return;
    blocks.push(<p key={idx}>{renderInline(line, `p-${idx}`)}</p>);
  });
  flushList("ul-end");

  return <div className="space-y-1.5">{blocks}</div>;
}

const SYSTEM_PROMPT = `You are FIRE-X Intelligence Assistant, an expert AI embedded in the FIRE-X geospatial fire intelligence platform for India.

You help users understand:
- Fire hotspot data from NASA FIRMS (MODIS/VIIRS satellite detections)
- Risk levels: CRITICAL (81-100), HIGH (51-80), ELEVATED (21-50), MODERATE (21-40), LOW (0-20)
- Classifications: Industrial Fire, Wildfire, Agricultural Burn, Persistent Heat Source
- FRP (Fire Radiative Power) in MW - indicator of fire intensity
- Industrial zones, refineries, factories, power plants, mines near hotspots
- Satellite validation, NDVI, burn area analysis
- Alerts and notification workflows

Be concise, use data-oriented language, and help users make operational decisions. If asked about specific hotspot IDs or zones, note that you cannot access live data directly - advise the user to check the dashboard.`;

export function AIChatPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "model", text: "Hello! I'm the FIRE-X Intelligence Assistant. Ask me anything about hotspot data, risk levels, satellite analysis, or fire classifications." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;
  const modelId = process.env.NEXT_PUBLIC_GEMINI_MODEL || "gemini-3.6-flash";

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100);
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    if (!apiKey) {
      setError("NEXT_PUBLIC_GEMINI_API_KEY is not set in .env.local");
      return;
    }

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({
        model: modelId,
        systemInstruction: SYSTEM_PROMPT,
      });

      // Build history (exclude the first assistant greeting, exclude latest user msg)
      const history = messages.slice(1).map((m) => ({
        role: m.role as "user" | "model",
        parts: [{ text: m.text }],
      }));

      const chat = model.startChat({ history });
      const result = await chat.sendMessage(text);
      const response = await result.response;
      const responseText = response.text();

      setMessages((prev) => [...prev, { role: "model", text: responseText }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to get response";
      setError(msg);
      setMessages((prev) => prev.slice(0, -1)); // remove the user msg on error
      setInput(text); // restore input
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed bottom-28 right-4 z-50 flex w-[360px] flex-col overflow-hidden rounded-2xl border border-base-border bg-base-panel shadow-2xl"
      style={{ maxHeight: "calc(100vh - 160px)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-base-border/60 px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-primary">FIRE-X Assistant</p>
          <p className="text-[10px] text-muted">Powered by Pragya-X</p>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-muted transition-colors hover:bg-base-raised hover:text-primary"
          aria-label="Close chat"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3" style={{ minHeight: 0 }}>
        {messages.map((m, i) => (
          <div key={i} className={cn("flex gap-2", m.role === "user" ? "flex-row-reverse" : "flex-row")}>
            {m.role === "model" && (
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent">
                <Bot className="h-3.5 w-3.5 text-white" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[78%] rounded-2xl px-3 py-2 text-sm leading-relaxed",
                m.role === "user"
                  ? "rounded-tr-sm bg-accent text-white"
                  : "rounded-tl-sm bg-base-raised/80 text-primary"
              )}
            >
              {m.role === "user" ? (
                m.text.split("\n").map((line, j) => (
                  <span key={j}>
                    {line}
                    {j < m.text.split("\n").length - 1 && <br />}
                  </span>
                ))
              ) : (
                <MarkdownMessage text={m.text} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-2">
            <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent">
              <Bot className="h-3.5 w-3.5 text-white" />
            </div>
            <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-base-raised/80 px-3 py-2.5">
              <span className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-muted"
                    style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
                  />
                ))}
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-2.5">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-base-border/60 p-3">
        {!apiKey && (
          <p className="mb-2 text-center text-[10px] text-amber-600">
            Add NEXT_PUBLIC_GEMINI_API_KEY to .env.local to enable chat
          </p>
        )}
        <div className="flex items-end gap-2 rounded-xl border border-base-border/70 bg-base-raised/60 px-3 py-2 focus-within:border-accent/50 transition-colors">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about hotspots, risk levels..."
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm text-primary placeholder:text-muted focus:outline-none"
            style={{ maxHeight: "80px" }}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent text-white transition-all hover:bg-accent/80 disabled:opacity-40"
            aria-label="Send message"
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
          </button>
        </div>
        <p className="mt-1.5 text-center text-[9px] text-muted/50">Enter to send · Shift+Enter for new line</p>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
