"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell, Brain, Building2, Database, Flame, History, LayoutDashboard,
  LogOut, MapPinned, Radar, Satellite, Settings, ShieldCheck, UserRound, UserCog, X,
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
  { href: "/system-health", label: "System status", icon: ShieldCheck },
  { href: "/profile", label: "Profile", icon: UserRound },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const renderLink = (item: (typeof MAIN_NAV)[number]) => {
    const active = pathname === item.href || (item.href !== "/" && !item.href.startsWith("/#") && pathname.startsWith(item.href));
    const Icon = item.icon;

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (item.href.startsWith("/#") && pathname === "/") {
        e.preventDefault();
        const targetId = item.href.substring(2);
        document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth" });
      }
      onClose();
    };

    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={handleClick}
        aria-current={active ? "page" : undefined}
        className={cn(
          "group mb-0.5 flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150",
          active
            ? "bg-gradient-to-r from-accent/20 to-accent/5 text-accent shadow-sm ring-1 ring-accent/20"
            : "text-muted hover:bg-base-raised/60 hover:text-primary"
        )}
      >
        <Icon className={cn("h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-110", active && "text-accent")} />
        <span>{item.label}</span>
        {active && (
          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent" />
        )}
      </Link>
    );
  };

  const content = (
    <div className="flex h-full flex-col" style={{ background: "linear-gradient(180deg, #07101f 0%, #04070d 100%)", borderRight: "1px solid rgba(30,41,59,0.8)" }}>
      {/* Logo */}
      <div className="flex items-center justify-between px-4 py-4" style={{ borderBottom: "1px solid rgba(30,41,59,0.6)" }}>
        <Link href="/" className="flex items-center gap-3" onClick={onClose}>
          <div
            className="flex h-9 w-9 items-center justify-center rounded-xl"
            style={{ background: "linear-gradient(135deg, #0284c7 0%, #7c3aed 100%)", boxShadow: "0 0 16px rgba(2,132,199,0.35)" }}
          >
            <Flame className="h-5 w-5 text-white" strokeWidth={2.2} />
          </div>
          <div>
            <span className="block text-sm font-bold tracking-widest text-white">FIRE-X</span>
            <span className="block text-[9px] uppercase tracking-[0.25em] text-sky-400/70">Fire Intelligence</span>
          </div>
        </Link>
        <button
          className="rounded-lg p-1.5 text-muted transition-colors hover:bg-base-raised lg:hidden"
          onClick={onClose}
          aria-label="Close menu"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3" aria-label="Main navigation">
        <p className="mb-1.5 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-muted/40">Main</p>
        {MAIN_NAV.map(renderLink)}

        <div className="my-3 mx-2 border-t border-base-border/30" />

        <details className="group/tools" open={TOOLS_NAV.some((item) => pathname.startsWith(item.href)) || pathname.startsWith("/admin")}>
          <summary className="mb-1.5 flex cursor-pointer list-none items-center gap-1 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-muted/40 hover:text-muted/70 transition-colors select-none">
            More Tools
            <svg className="ml-auto h-3 w-3 transition-transform group-open/tools:rotate-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M9 18l6-6-6-6" />
            </svg>
          </summary>
          {TOOLS_NAV.map(renderLink)}
          {user?.role === "admin" && renderLink({ href: "/admin", label: "Admin Panel", icon: UserCog })}
        </details>
      </nav>

      {/* User footer */}
      <div className="p-3" style={{ borderTop: "1px solid rgba(30,41,59,0.6)" }}>
        <Link
          href="/profile"
          className="flex items-center gap-2.5 rounded-xl p-2.5 transition-colors hover:bg-base-raised/50"
          onClick={onClose}
        >
          <span
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
            style={{ background: "linear-gradient(135deg, #0284c7 0%, #7c3aed 100%)" }}
          >
            {user?.name?.charAt(0) ?? "U"}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-primary">{user?.name}</p>
            <p className="text-[10px] uppercase tracking-wider text-muted/60">{user?.role}</p>
          </div>
          <button
            onClick={(e) => {
              e.preventDefault();
              logout();
            }}
            className="rounded-lg p-1.5 text-muted transition-colors hover:bg-base-raised hover:text-critical"
            aria-label="Log out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </Link>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop */}
      <aside className="hidden w-[220px] shrink-0 lg:block">{content}</aside>
      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
          <aside className="absolute left-0 top-0 h-full w-64 animate-slideIn">{content}</aside>
        </div>
      )}
    </>
  );
}