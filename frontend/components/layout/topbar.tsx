"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Bell, Menu, Search } from "lucide-react";
import { searchHotspots } from "@/lib/search";
import { getNotifications, markNotificationsRead, markNotificationRead } from "@/lib/api";
import { Button, Dialog } from "@/components/ui/primitives";
import { NotificationCenter } from "@/components/notification-center";
import { useSSE } from "@/hooks/useSSE";
import type { NotificationItem } from "@/lib/types";

export function Topbar({ onMenu, pathname }: { onMenu: () => void; pathname: string }) {
  const router = useRouter();
  const [now, setNow] = useState(new Date());
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  useEffect(() => {
    if (theme === "dark") document.documentElement.classList.add("dark-theme");
    else document.documentElement.classList.remove("dark-theme");
  }, [theme]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ label: string; href: string; meta: string }[]>([]);
  const [searching, setSearching] = useState(false);
  const { latest } = useSSE(10);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    getNotifications().then((r) => {
      setNotifications(r.items);
      setUnread(r.unread);
    }).catch(() => undefined);
    return () => clearInterval(t);
  }, []);

  // Live notifications via SSE
  useEffect(() => {
    if (latest?.type === "notification") {
      const n = latest.data as NotificationItem;
      setNotifications((prev) => [n, ...prev].slice(0, 40));
      setUnread((u) => u + 1);
    }
  }, [latest]);

  useEffect(() => {
    if (searchOpen) setTimeout(() => inputRef.current?.focus(), 50);
  }, [searchOpen]);

  const runSearch = async (q: string) => {
    setQuery(q);
    if (q.trim().length < 2) {
      setResults([]);
      return;
    }
    setSearching(true);
    try {
      setResults(await searchHotspots(q));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-base-border bg-base-panel px-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenu} aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </Button>
        <button
          onClick={() => setSearchOpen(true)}
          className="hidden h-9 w-72 items-center gap-2 rounded-md border border-base-border bg-base-raised/70 px-3 text-left text-sm text-slate-500 transition-colors hover:border-accent/50 md:flex"
        >
          <Search className="h-4 w-4" />
          Search hotspots, zones, states...
          <kbd className="ml-auto rounded border border-base-border px-1 text-[9px] text-slate-600">/</kbd>
        </button>
      </div>

      <div className="flex items-center gap-2.5">
        <div className="hidden text-right sm:block">
          <p className="font-mono text-xs text-slate-700">
            {now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
          </p>
          <p className="font-mono text-[10px] text-slate-500">{now.toLocaleTimeString("en-IN", { hour12: false })} IST</p>
        </div>

        <div className="relative">
          <Button variant="ghost" size="icon" onClick={() => setTheme(t => t === "light" ? "dark" : "light")} aria-label="Toggle theme" className="rounded-full">
          <span className="text-xs font-bold">{theme === "dark" ? "☀" : "☾"}</span>
        </Button>
        <Button variant="ghost" size="icon" onClick={() => setOpen(!open)} aria-label={`Notifications, ${unread} unread`} className="relative">
            <Bell className="h-5 w-5" />
            {unread > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-critical px-1 text-[9px] font-bold text-slate-900">
                {unread > 9 ? "9+" : unread}
              </span>
            )}
          </Button>
          {open && (
            <NotificationCenter
              items={notifications}
              onClose={() => setOpen(false)}
              onMarkRead={() => { markNotificationsRead().then(() => setUnread(0)).catch(() => undefined); setOpen(false); }}
              onItemRead={(id) => {
                markNotificationRead(id).catch(() => undefined);
                setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
                setUnread((u) => Math.max(0, u - 1));
              }}
            />
          )}
        </div>
      </div>

      {/* Global search dialog */}
      <Dialog open={searchOpen} onClose={() => setSearchOpen(false)} title="Global search">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 shrink-0 text-slate-500" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => runSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "/") e.preventDefault();
            }}
            placeholder="Hotspot ID (HX-0012), state, district, zone..."
            className="h-9 w-full rounded-md border border-base-border bg-base-raised/80 px-3 text-sm text-slate-900 focus:border-accent/60 focus:outline-none"
          />
        </div>
        <div className="mt-3 max-h-80 overflow-y-auto">
          {searching && <p className="px-1 py-2 text-xs text-slate-500">Searching...</p>}
          {!searching && results.length === 0 && query.trim().length >= 2 && (
            <p className="px-1 py-2 text-xs text-slate-500">No matches found.</p>
          )}
          {results.map((r, i) => (
            <button
              key={i}
              onClick={() => {
                setSearchOpen(false);
                setQuery("");
                router.push(r.href);
              }}
              className="flex w-full items-center justify-between rounded px-2 py-2 text-left hover:bg-slate-100/60"
            >
              <span className="text-sm text-slate-900">{r.label}</span>
              <span className="text-[10px] text-slate-500">{r.meta}</span>
            </button>
          ))}
        </div>
      </Dialog>
    </header>
  );
}
