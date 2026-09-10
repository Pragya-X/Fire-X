"use client";

import { useRouter } from "next/navigation";
import { BellRing } from "lucide-react";
import type { NotificationItem } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

const toneDot: Record<string, string> = {
  critical: "bg-critical",
  error: "bg-critical",
  success: "bg-low",
  warning: "bg-moderate",
  info: "bg-info",
};

function hrefFor(n: NotificationItem): string | null {
  if (n.entity === "alert") return "/alerts";
  if (n.entity === "hotspot" && n.entity_id) return `/hotspots?search=${encodeURIComponent(n.entity_id)}`;
  if (n.entity === "ingest") return "/ingestion";
  return null;
}

export function NotificationCenter({
  items,
  onClose,
  onMarkRead,
  onItemRead,
}: {
  items: NotificationItem[];
  onClose: () => void;
  onMarkRead: () => void;
  onItemRead: (id: number) => void;
}) {
  const router = useRouter();

  const open = (n: NotificationItem) => {
    if (!n.read) onItemRead(n.id);
    const href = hrefFor(n);
    onClose();
    if (href) router.push(href);
  };

  return (
    <div className="absolute right-0 top-11 z-50 w-80 rounded-lg border border-base-border bg-base-panel shadow-panel" role="menu" aria-label="Notifications">
      <div className="flex items-center justify-between border-b border-base-border/70 px-3 py-2">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-primary">
          <BellRing className="h-3.5 w-3.5 text-accent" /> Notifications
        </span>
        <button onClick={onMarkRead} className="text-[10px] text-accent hover:underline">
          Mark all read
        </button>
      </div>
      <div className="max-h-80 overflow-y-auto">
        {items.length === 0 && <p className="px-3 py-6 text-center text-xs text-muted">No notifications yet.</p>}
        {items.map((n) => {
          const clickable = hrefFor(n) !== null;
          const inner = (
            <>
              <span className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", n.read ? "bg-slate-600" : toneDot[n.severity] || "bg-info")} />
              <div className="min-w-0">
                <p className={cn("text-xs", n.read ? "font-normal text-muted" : "font-semibold text-slate-100")}>{n.title}</p>
                <p className="mt-0.5 line-clamp-2 text-[11px] text-muted">{n.message}</p>
                <p className="mt-0.5 text-[9px] text-muted">{timeAgo(n.created_at)}</p>
              </div>
            </>
          );
          return clickable ? (
            <button
              key={n.id}
              onClick={() => open(n)}
              className="flex w-full gap-2.5 border-b border-base-border/40 px-3 py-2.5 text-left transition-colors last:border-0 hover:bg-base-raised/40"
            >
              {inner}
            </button>
          ) : (
            <div key={n.id} className="flex gap-2.5 border-b border-base-border/40 px-3 py-2.5 last:border-0">
              {inner}
            </div>
          );
        })}
      </div>
      <button onClick={onClose} className="w-full border-t border-base-border/70 py-1.5 text-[10px] text-muted hover:text-secondary">
        Close
      </button>
    </div>
  );
}