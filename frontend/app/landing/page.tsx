"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight, BarChart3, Bell, Brain, ChevronRight, Flame, Globe,
  MapPin, Satellite, Shield, Zap, Users, Clock, Eye,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

const FEATURES = [
  {
    icon: Satellite,
    title: "NASA FIRMS Integration",
    desc: "Real-time satellite thermal detection feed processing 50K+ daily hotspots from VIIRS and MODIS sensors across India.",
  },
  {
    icon: Brain,
    title: "AI Classification Engine",
    desc: "HistGradientBoosting ML model classifies fires vs industrial sources vs agricultural burns with 95%+ accuracy in <2ms.",
  },
  {
    icon: Globe,
    title: "GIS Command Center",
    desc: "Interactive MapLibre geospatial dashboard with real-time hotspot visualization, industrial zone overlays, and risk heatmaps.",
  },
  {
    icon: BarChart3,
    title: "Risk Analytics",
    desc: "Multi-factor risk scoring combining thermal intensity, proximity to infrastructure, land cover, and historical persistence patterns.",
  },
  {
    icon: Bell,
    title: "Smart Alert System",
    desc: "Multi-channel incident alerts via in-app notifications, SSE live streaming, and SMTP email with configurable severity thresholds.",
  },
  {
    icon: Shield,
    title: "Evidence-Based Decisions",
    desc: "Hybrid rule + ML decision engine with SHAP explainability. Every classification includes transparent reasoning and confidence scores.",
  },
];

const STATS = [
  { value: "50K+", label: "Daily Detections", icon: Satellite },
  { value: "<2ms", label: "Inference Time", icon: Zap },
  { value: "95%+", label: "ML Accuracy", icon: Brain },
  { value: "24/7", label: "Monitoring", icon: Clock },
  { value: "61+", label: "API Endpoints", icon: Globe },
  { value: "5", label: "Alert Channels", icon: Bell },
];

const PIPELINE = [
  { label: "Histogram Binning", desc: "Bins features into 256 integer buckets for 10-100x faster split evaluation." },
  { label: "Sequential Boosting", desc: "Each tree corrects the residual errors of the previous one - no redundant computation." },
  { label: "Native NaN Handling", desc: "Missing satellite channels are handled natively, keeping the data pipeline simple." },
];

const BENCHMARKS = [
  { metric: "Training speed", rf: "4.2s", hgb: "0.8s", gain: "5x faster", hgbPct: 20 },
  { metric: "Inference / sample", rf: "12ms", hgb: "2ms", gain: "6x faster", hgbPct: 17 },
  { metric: "Memory usage", rf: "180 MB", hgb: "25 MB", gain: "7x less", hgbPct: 14 },
  { metric: "Accuracy", rf: "94.2%", hgb: "95.1%", gain: "Higher", hgbPct: 95 },
];

const TECH = [
  "Python / FastAPI", "Next.js / React", "scikit-learn", "NASA FIRMS",
  "MapLibre GL", "SQLAlchemy", "Tailwind CSS", "WebSocket / SSE",
];

const BRAND =
  "flex h-9 w-9 items-center justify-center rounded-lg bg-accent";

export default function LandingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace("/");
      return;
    }
    const handleScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [user, router]);

  return (
    <div className="min-h-screen bg-black text-zinc-300">
      {/* Navbar */}
      <nav
        className={`fixed left-0 right-0 top-0 z-50 transition-colors duration-300 ${
          scrolled ? "border-b border-white/10 bg-black/90 backdrop-blur" : ""
        }`}
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className={BRAND}>
              <Flame className="h-5 w-5 text-white" fill="currentColor" strokeWidth={2} />
            </div>
            <span className="text-[15px] font-semibold tracking-[0.18em] text-white">FIRE-X</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login" className="rounded-lg px-4 py-2 text-[13px] font-medium text-slate-300 transition-colors hover:text-white">
              Sign in
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-white px-4 py-2 text-[13px] font-semibold text-slate-900 transition-colors hover:bg-slate-200"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pb-24 pt-36">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% -10%, rgba(14,165,233,0.12), transparent 45%), radial-gradient(circle at 85% 15%, rgba(124,58,237,0.08), transparent 45%)",
          }}
        />
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-full opacity-[0.15]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(148,163,184,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.07) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage: "radial-gradient(ellipse at top, black 30%, transparent 75%)",
            WebkitMaskImage: "radial-gradient(ellipse at top, black 30%, transparent 75%)",
          }}
        />

        <div className="relative mx-auto max-w-6xl px-6 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              SIH 2026 · PS 26162 · NTRO · Disaster Management
            </span>
          </div>

          <h1 className="mx-auto mb-6 max-w-3xl text-4xl font-bold leading-[1.12] tracking-tight text-white sm:text-5xl lg:text-[56px]">
            Fire intelligence you can act on
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-[16px] leading-relaxed text-slate-400">
            FIRE-X detects, classifies, and tracks industrial fires and thermal anomalies in
            real time — combining NASA FIRMS satellite data, geospatial mapping, and
            gradient-boosted ML classification.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/signup"
              className="flex items-center gap-2 rounded-lg bg-white px-6 py-3 text-[14px] font-semibold text-slate-900 transition-colors hover:bg-slate-200"
            >
              Start free <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/login"
              className="flex items-center gap-2 rounded-lg border border-white/15 px-6 py-3 text-[14px] font-medium text-slate-200 transition-colors hover:border-white/30 hover:bg-white/[0.04]"
            >
              <Eye className="h-4 w-4" /> Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-y border-white/10 bg-white/[0.02]">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-x-4 gap-y-8 px-6 py-10 sm:grid-cols-3 lg:grid-cols-6">
          {STATS.map((s, i) => (
            <div key={i} className="text-center">
              <p className="text-2xl font-semibold text-white">{s.value}</p>
              <p className="mt-1 text-[10px] uppercase tracking-wider text-slate-500">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-14 max-w-2xl">
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-400">
              Core capabilities
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Everything you need for fire intelligence
            </h2>
          </div>

          <div className="grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <div key={i} className="group bg-black p-6 transition-colors hover:bg-[#0d0d0f]">
                <f.icon className="mb-4 h-5 w-5 text-sky-400" strokeWidth={1.8} />
                <h3 className="mb-2 text-[15px] font-semibold text-white">{f.title}</h3>
                <p className="text-[13px] leading-relaxed text-slate-400">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ML Architecture Highlight */}
      <section className="border-y border-white/10 bg-white/[0.02] py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-400">
                Optimized ML pipeline
              </p>
              <h2 className="mb-4 text-3xl font-bold tracking-tight text-white">
                Why HistGradientBoosting?
              </h2>
              <p className="mb-6 text-[14px] leading-relaxed text-slate-400">
                We replaced traditional Random Forest — which builds 200+ independent trees using
                brute-force random loops — with scikit-learn&apos;s{" "}
                <strong className="text-white">HistGradientBoostingClassifier</strong>, a
                histogram-based gradient boosting architecture purpose-built for production speed.
              </p>
              <div className="space-y-3">
                {PIPELINE.map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400" />
                    <div>
                      <p className="text-[13px] font-semibold text-white">{item.label}</p>
                      <p className="text-[12px] leading-relaxed text-slate-500">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-black p-6">
              <p className="mb-5 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                Random Forest vs HistGradientBoosting
              </p>
              <div className="space-y-5">
                {BENCHMARKS.map((row) => (
                  <div key={row.metric}>
                    <div className="mb-1.5 flex items-center justify-between text-[12px]">
                      <span className="text-slate-400">{row.metric}</span>
                      <span className="font-medium text-emerald-400">{row.gain}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-32 shrink-0 text-[11px] text-slate-500">Random Forest</span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                        <div className="h-full w-full rounded-full bg-slate-600" />
                      </div>
                      <span className="w-14 shrink-0 text-right font-mono text-[11px] text-slate-400">{row.rf}</span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-3">
                      <span className="w-32 shrink-0 text-[11px] text-sky-400">HistGradientBoosting</span>
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                        <div className="h-full rounded-full bg-sky-500" style={{ width: `${row.hgbPct}%` }} />
                      </div>
                      <span className="w-14 shrink-0 text-right font-mono text-[11px] text-sky-300">{row.hgb}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="mb-8 text-2xl font-bold tracking-tight text-white">Built with modern technology</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {TECH.map((t, i) => (
              <span
                key={i}
                className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-[12px] font-medium text-slate-400 transition-colors hover:border-white/20 hover:text-slate-200"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/10 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-white">Ready to detect faster?</h2>
          <p className="mb-8 text-[14px] text-slate-400">
            Join FIRE-X and get access to real-time fire intelligence powered by NASA satellites and AI.
          </p>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-7 py-3.5 text-[14px] font-semibold text-slate-900 transition-colors hover:bg-slate-200"
          >
            Create free account <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6">
          <div className="flex items-center gap-2">
            <Flame className="h-4 w-4 text-sky-400" fill="currentColor" />
            <span className="text-[12px] font-semibold tracking-wider text-white">FIRE-X</span>
            <span className="text-[10px] text-slate-600">© 2026 Team Pragya-X</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-slate-600">
            <span>Smart India Hackathon 2026</span>
            <span>PS 26162 · NTRO</span>
            <span>Disaster Management</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
