"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Bell, Building2, Flame, Menu, Search, ShieldCheck } from "lucide-react";
import { searchHotspots } from "@/lib/search";
import { getNotifications, markNotificationsRead, markNotificationRead } from "@/lib/api";
import { Dialog, useToast } from "@/components/ui/primitives";
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
      {/* Org strip — slim ministry-style bar above the main header */}
      <div className="flex h-7 shrink-0 items-center justify-between border-b border-base-border bg-base px-4 text-[10px] text-muted">
        <p className="flex items-center gap-1.5">
          <Building2 className="h-3 w-3" />
          <span className="font-medium text-secondary">National Fire Intelligence Grid</span>
          <span className="hidden sm:inline">· Smart India Hackathon 2026 · PS 26162 · NTRO</span>
        </p>
        <p className="hidden font-mono md:block">
          {now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })} ·{" "}
          {now.toLocaleTimeString("en-IN", { hour12: false })} IST
        </p>
      </div>

      {/* Main header — brand block left, search center, status pills right */}
      <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-base-border bg-base-panel px-4">
        {/* Brand block */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMenu}
            className="rounded-lg p-1.5 text-muted transition-colors hover:bg-base-raised lg:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent">
              <Flame className="h-5 w-5 text-white" fill="currentColor" strokeWidth={2} />
            </div>
            <div className="hidden sm:block">
              <p className="text-[15px] font-bold leading-tight tracking-[0.14em] text-primary">FIRE-X</p>
              <p className="text-[10px] leading-tight text-muted">
                AI Fire Intelligence &amp; Risk Platform
              </p>
            </div>
          </Link>

          <span className="ml-2 hidden items-center gap-1.5 rounded-md border border-base-border bg-base px-2.5 py-1 lg:flex">
            <ShieldCheck className="h-3.5 w-3.5 text-low" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-secondary">
              Command Center Portal
            </span>
          </span>
        </div>

        {/* Search */}
        <button
          onClick={() => setSearchOpen(true)}
          className="hidden h-9 w-full max-w-sm items-center gap-2 rounded-lg border border-base-border bg-base px-3 text-left text-[13px] text-muted transition-colors hover:border-accent/40 md:flex"
        >
          <Search className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1 truncate">Search hotspots, zones, districts…</span>
          <kbd className="rounded border border-base-border px-1.5 py-0.5 text-[9px] text-muted/60">/</kbd>
        </button>

        {/* Right cluster */}
        <div className="flex items-center gap-1.5">
          <span className="mr-1 hidden items-center gap-1.5 rounded-full border border-low/30 bg-low/10 px-2.5 py-1 sm:flex">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-low opacity-60" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-low" />
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-low">Live · Synced</span>
          </span>

          <div className="hidden text-right sm:block">
            <p className="font-mono text-[11px] font-medium text-secondary">
              {now.toLocaleTimeString("en-IN", { hour12: false })}
            </p>
            <p className="font-mono text-[9px] text-muted/60">IST</p>
          </div>

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
