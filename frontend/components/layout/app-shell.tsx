"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { SystemStatusBar } from "@/components/system-status";
import { AIChatPanel } from "@/components/ai-chat-panel";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  // Initialize dark theme immediately on mount
  useEffect(() => {
    document.documentElement.classList.add("dark-theme");
  }, []);

  useEffect(() => {
    if (!loading && !user) router.replace("/landing");
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg border border-base-border bg-slate-800">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
            </svg>
          </div>
          <p className="text-xs text-muted">Loading FIRE-X...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenu={() => setSidebarOpen(true)} pathname={pathname} />
        <main className="min-h-0 flex-1 overflow-y-auto p-4">{children}</main>
        <SystemStatusBar />
      </div>

      {/* Floating AI chat button — visible on every page */}
      <button
        onClick={() => setChatOpen((v) => !v)}
        aria-label="Toggle AI chat"
        title="FIRE-X AI Assistant"
        className="fixed bottom-12 right-4 z-50 flex h-12 w-12 items-center justify-center rounded-full shadow-xl transition-all duration-200 hover:scale-110 active:scale-95"
        style={{
          background: chatOpen
            ? "linear-gradient(135deg, #0284c7 0%, #7c3aed 100%)"
            : "linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%)",
          boxShadow: chatOpen
            ? "0 0 0 4px rgba(2,132,199,0.25), 0 8px 24px rgba(2,132,199,0.5)"
            : "0 0 0 2px rgba(2,132,199,0.15), 0 8px 24px rgba(2,132,199,0.35)",
        }}
      >
        <Sparkles
          className="h-5 w-5 text-white transition-transform duration-300"
          style={{ transform: chatOpen ? "rotate(20deg)" : "rotate(0deg)" }}
        />
      </button>

      {/* AI chat panel */}
      <AIChatPanel open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}