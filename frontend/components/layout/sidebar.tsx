"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell, Brain, Building2, Database, Flame, History, LayoutDashboard, LogOut,
  MapPinned, Radar, Satellite, Settings, ShieldCheck, UserRound, X,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const MAIN_NAV = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/#live-map", label: "Live Map", icon: MapPinned },
  { href: "/event-workspace", label: "Event Details", icon: ShieldCheck },
  { href: "/analytics", label: "Analytics", icon: Radar },
  { href: "/ai-intelligence", label: "AI Results", icon: Brain },
  { href: "/reports", label: "Reports", icon: MapPinned },
  { href: "/settings", label: "Settings", icon: Settings },
];

const TOOLS_NAV = [
  { href: "/hotspots", label: "Hotspot records", icon: Flame },
  { href: "/industrial-zones", label: "Industrial zones", icon: Building2 },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/historical", label: "Historical records", icon: History },
  { href: "/ingestion", label: "Data ingestion", icon: Database },
  { href: "/satellite-validation", label: "Satellite evidence", icon: Satellite },
  { href: "/copilot", label: "Data Q&A", icon: Brain },
  { href: "/system-health", label: "System status", icon: ShieldCheck },
  { href: "/profile", label: "Profile", icon: UserRound },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const renderLink = (item: (typeof MAIN_NAV)[number]) => {
    const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
    const Icon = item.icon;
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={onClose}
        aria-current={active ? "page" : undefined}
        className={cn(
          "mb-0.5 flex items-center gap-2.5 rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
          active ? "bg-slate-600 text-white" : "text-slate-600 hover:bg-slate-100/50 hover:text-slate-900"
        )}
      >
        <Icon className="h-4 w-4" />
        {item.label}
      </Link>
    );
  };

  const content = (
    <div className="flex h-full flex-col border-r border-base-border/70 bg-base-panel/90">
      <div className="flex items-center justify-between border-b border-base-border/70 px-4 py-4">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-md border border-base-border bg-slate-700">
            <Flame className="h-5 w-5 text-accent" strokeWidth={2.2} />
          </span>
          <span>
            <span className="block text-base font-bold tracking-wider text-slate-700">FIRE-X</span>
            <span className="block text-[9px] uppercase tracking-[0.2em] text-slate-400">Fire Intelligence</span>
          </span>
        </Link>
        <button className="rounded p-1 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={onClose} aria-label="Close menu">
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3" aria-label="Main navigation">
        {MAIN_NAV.map(renderLink)}
        <details className="mt-3" open={TOOLS_NAV.some((item) => pathname.startsWith(item.href))}>
          <summary className="cursor-pointer rounded px-3 py-2 text-xs text-slate-600 hover:text-slate-900">
            More tools
          </summary>
          {TOOLS_NAV.map(renderLink)}
        </details>
      </nav>

      <div className="border-t border-base-border/70 p-3">
        <Link href="/profile" className="flex items-center gap-2.5 rounded-md bg-base-raised/60 p-2.5 transition-colors hover:bg-slate-100">
          <span className="flex h-8 w-8 items-center justify-center rounded-full border border-base-border bg-slate-700 text-xs font-bold text-accent">
            {user?.name?.charAt(0) ?? "U"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-slate-900">{user?.name}</p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{user?.role}</p>
          </div>
          <button
            onClick={(e) => {
              e.preventDefault();
              logout();
            }}
            className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-critical"
            aria-label="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </Link>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside className="hidden w-60 shrink-0 lg:block">{content}</aside>
      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/80" onClick={onClose} />
          <aside className="absolute left-0 top-0 h-full w-64">{content}</aside>
        </div>
      )}
    </>
  );
}