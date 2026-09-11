"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Bell, Menu, Search } from "lucide-react";
import { searchHotspots } from "@/lib/search";
import { getNotifications, markNotificationsRead, markNotificationRead } from "@/lib/api";
import { applyTheme, getTheme, type Theme } from "@/lib/theme";
import { Button, Dialog, useToast } from "@/components/ui/primitives";
import { NotificationCenter } from "@/components/notification-center";
import { useSSE } from "@/hooks/useSSE";
import type { NotificationItem } from "@/lib/types";

export function Topbar({ onMenu, pathname }: { onMenu: () => void; pathname: string }) {
  const router = useRouter();
  const { push } = useToast();
  const [now, setNow] = useState(new Date());
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [notifOpen, setNotifOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    setTheme(getTheme());
  }, []);

  const toggleTheme = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  };

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

  useEffect(() => {
    if (latest?.type === "notification") {
      const n = latest.data as NotificationItem;
      setNotifications((prev) => [n, ...prev].slice(0, 40));
      setUnread((u) => u + 1);
      
      // Trigger instant toast popup
      push({
        title: n.title,
        message: n.message,
        tone: n.severity === "CRITICAL" || n.severity === "HIGH" ? "critical" : "info"
      });
    }
  }, [latest, push]);

  useEffect(() => {
    if (searchOpen) setTimeout(() => inputRef.current?.focus(), 50);
  }, [searchOpen]);

  // keyboard shortcut: / opens search
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "/" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const runSearch = async (q: string) => {
    setQuery(q);
    if (q.trim().length < 2) { setResults([]); return; }
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
    <>
      <header
        className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-base-border bg-base-panel/80 px-4 backdrop-blur"
      >
        {/* Left */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMenu}
            className="rounded-lg p-1.5 text-muted transition-colors hover:bg-base-raised lg:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Search bar */}
          <button
            onClick={() => setSearchOpen(true)}
            className="hidden h-8 w-64 items-center gap-2 rounded-lg border border-base-border/60 bg-base-raised/30 px-3 text-left text-[13px] text-muted transition-all hover:border-accent/40 hover:bg-base-raised/60 md:flex"
          >
            <Search className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1">Search hotspots, zones...</span>
            <kbd className="rounded border border-base-border/60 px-1.5 py-0.5 text-[9px] text-muted/60">/</kbd>
          </button>
        </div>

        {/* Right */}
        <div className="flex items-center gap-1.5">
          {/* Date/time */}
          <div className="hidden text-right sm:block mr-1">
            <p className="font-mono text-[11px] font-medium text-secondary">
              {now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
            </p>
            <p className="font-mono text-[9px] text-muted/60">
              {now.toLocaleTimeString("en-IN", { hour12: false })} IST
            </p>
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-base-raised hover:text-primary"
            aria-label="Toggle theme"
          >
            <span className="text-[13px]">{theme === "dark" ? "☀" : "☾"}</span>
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setNotifOpen(!notifOpen)}
              className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-base-raised hover:text-primary"
              aria-label={`Notifications, ${unread} unread`}
            >
              <Bell className="h-4 w-4" />
              {unread > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-critical px-1 text-[9px] font-bold text-white">
                  {unread > 9 ? "9+" : unread}
                </span>
              )}
            </button>
            {notifOpen && (
              <NotificationCenter
                items={notifications}
                onClose={() => setNotifOpen(false)}
                onMarkRead={() => {
                  markNotificationsRead().then(() => setUnread(0)).catch(() => undefined);
                  setNotifOpen(false);
                }}
                onItemRead={(id) => {
                  markNotificationRead(id).catch(() => undefined);
                  setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
                  setUnread((u) => Math.max(0, u - 1));
                }}
              />
            )}
          </div>
        </div>
      </header>

      {/* Global search dialog */}
      <Dialog open={searchOpen} onClose={() => setSearchOpen(false)} title="Global search">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 shrink-0 text-muted" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => runSearch(e.target.value)}
            onKeyDown={(e) => { if (e.key === "/") e.preventDefault(); }}
            placeholder="Hotspot ID (HX-0012), state, district, zone..."
            className="h-9 w-full rounded-md border border-base-border bg-base-raised/80 px-3 text-sm text-primary focus:border-accent/60 focus:outline-none"
          />
        </div>
        <div className="mt-3 max-h-80 overflow-y-auto">
          {searching && <p className="px-1 py-2 text-xs text-muted">Searching...</p>}
          {!searching && results.length === 0 && query.trim().length >= 2 && (
            <p className="px-1 py-2 text-xs text-muted">No matches found.</p>
          )}
          {results.map((r, i) => (
            <button
              key={i}
              onClick={() => { setSearchOpen(false); setQuery(""); router.push(r.href); }}
              className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left transition-colors hover:bg-base-raised/60"
            >
              <span className="text-sm text-primary">{r.label}</span>
              <span className="text-[10px] text-muted">{r.meta}</span>
            </button>
          ))}
        </div>
      </Dialog>
    </>
  );
}
