"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowRight, BarChart3, Bell, Brain, ChevronRight, Flame, Globe,
  MapPin, Satellite, Shield, Zap, Clock, Eye, Radio, FileText, Siren,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

const FEATURES = [
  {
    icon: Satellite,
    title: "NASA FIRMS Integration",
    desc: "Real-time thermal detection feed processing 50K+ daily hotspots from VIIRS and MODIS sensors across India.",
  },
  {
    icon: Brain,
    title: "AI Classification Engine",
    desc: "HistGradientBoosting model separates industrial fires, wildfires, and agricultural burns with 95%+ accuracy in under 2ms.",
  },
  {
    icon: Globe,
    title: "GIS Command Center",
    desc: "Interactive MapLibre dashboard with live hotspot visualization, industrial zone overlays, and risk heatmaps.",
  },
  {
    icon: BarChart3,
    title: "Risk Analytics",
    desc: "Multi-factor scoring combining thermal intensity, infrastructure proximity, land cover, and persistence patterns.",
  },
  {
    icon: Bell,
    title: "Smart Alert System",
    desc: "Multi-channel incident alerts through in-app notifications, SSE live streaming, and SMTP email with severity thresholds.",
  },
  {
    icon: Shield,
    title: "Evidence-Based Decisions",
    desc: "Hybrid rule + ML decision engine with SHAP explainability — every classification carries reasoning and confidence.",
  },
];

const WORKFLOW = [
  {
    icon: Radio,
    step: "01",
    title: "Detect",
    desc: "NASA FIRMS satellite passes are ingested every 2 minutes and geolocated against India's industrial landscape.",
  },
  {
    icon: Brain,
    step: "02",
    title: "Classify",
    desc: "The ML engine scores each hotspot — fire type, confidence, and risk tier — with SHAP-backed explanations.",
  },
  {
    icon: Siren,
    step: "03",
    title: "Respond",
    desc: "Critical events raise alerts instantly, generate incident reports, and surface full intelligence for operators.",
  },
];

const STATS = [
  { value: "50K+", label: "Daily Detections" },
  { value: "<2ms", label: "Inference Time" },
  { value: "95%+", label: "ML Accuracy" },
  { value: "24/7", label: "Monitoring" },
  { value: "61+", label: "API Endpoints" },
  { value: "5", label: "Alert Channels" },
];

const PIPELINE = [
  { label: "Histogram Binning", desc: "Bins features into 256 integer buckets for 10-100x faster split evaluation." },
  { label: "Sequential Boosting", desc: "Each tree corrects the residual errors of the previous one — no redundant computation." },
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

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#workflow", label: "Workflow" },
  { href: "#ml", label: "ML Engine" },
  { href: "#tech", label: "Technology" },
];

export default function LandingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace("/");
      return;
    }
    const handleScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [user, router]);

  return (
    <div className="min-h-screen bg-white text-slate-600">
      {/* Top gov strip */}
      <div className="border-b border-slate-100 bg-slate-900 text-slate-300">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-1.5 text-[11px]">
          <span>Smart India Hackathon 2026 · Problem Statement 26162 · NTRO</span>
          <span className="hidden sm:inline">Disaster Management</span>
        </div>
      </div>

      {/* Navbar */}
      <nav
        className={`sticky top-0 z-50 bg-white/95 backdrop-blur transition-shadow duration-300 ${
          scrolled ? "border-b border-slate-200 shadow-sm" : "border-b border-slate-100"
        }`}
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link href="/landing" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-sky-600 to-cyan-600 shadow-sm">
              <Flame className="h-5 w-5 text-white" fill="currentColor" strokeWidth={2} />
            </div>
            <div>
              <span className="block text-[15px] font-bold leading-tight tracking-[0.14em] text-slate-900">FIRE-X</span>
              <span className="block text-[10px] leading-tight text-slate-500">AI Fire Intelligence</span>
            </div>
          </Link>

          <div className="hidden items-center gap-6 lg:flex">
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href} className="text-[13px] font-medium text-slate-600 transition-colors hover:text-slate-900">
                {l.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Link href="/login" className="rounded-lg px-4 py-2 text-[13px] font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900">
              Sign in
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-accent px-4 py-2 text-[13px] font-semibold text-white shadow-sm transition-colors hover:bg-accent/90"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero — split layout with product mock */}
      <section className="relative overflow-hidden border-b border-slate-100">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(circle at 12% 0%, rgba(14,165,233,0.09), transparent 42%), radial-gradient(circle at 95% 20%, rgba(6,182,212,0.07), transparent 45%)",
          }}
        />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-14 lg:grid-cols-2 lg:pb-24 lg:pt-20">
          {/* Copy */}
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3.5 py-1.5">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-70" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-700">
                Live NASA FIRMS feed · Synced every 2 min
              </span>
            </div>

            <h1 className="mb-5 text-4xl font-extrabold leading-[1.1] tracking-tight text-slate-900 sm:text-[52px]">
              Fire intelligence<br />
              <span className="text-accent">you can act on.</span>
            </h1>

            <p className="mb-8 max-w-lg text-[16px] leading-relaxed text-slate-600">
              FIRE-X detects, classifies, and tracks industrial fires and thermal anomalies in
              real time — fusing NASA satellite data, geospatial mapping, and gradient-boosted
              machine learning into one command center.
            </p>

            <div className="mb-8 flex flex-wrap items-center gap-3">
              <Link
                href="/signup"
                className="flex items-center gap-2 rounded-lg bg-accent px-6 py-3 text-[14px] font-semibold text-white shadow-sm shadow-sky-600/20 transition-colors hover:bg-accent/90"
              >
                Start free <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/login"
                className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-6 py-3 text-[14px] font-medium text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-50"
              >
                <Eye className="h-4 w-4" /> Sign in
              </Link>
            </div>

            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[12px] text-slate-500">
              <span className="flex items-center gap-1.5"><Shield className="h-3.5 w-3.5 text-emerald-600" /> Rule + ML decision engine</span>
              <span className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5 text-emerald-600" /> 24/7 automated monitoring</span>
              <span className="flex items-center gap-1.5"><FileText className="h-3.5 w-3.5 text-emerald-600" /> One-click incident reports</span>
            </div>
          </div>

          {/* Product mock — pure CSS dashboard preview */}
          <div className="relative hidden lg:block">
            <div className="absolute -inset-6 rounded-3xl bg-gradient-to-br from-sky-100/70 to-cyan-50/40 blur-2xl" />
            <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-900/5">
              {/* Window header */}
              <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                <span className="ml-3 text-[11px] font-medium text-slate-400">FIRE-X · Live Operations</span>
              </div>
              <div className="p-4">
                {/* Fake map */}
                <div className="relative h-56 overflow-hidden rounded-xl bg-gradient-to-br from-sky-50 via-slate-50 to-cyan-50">
                  <div
                    className="absolute inset-0 opacity-50"
                    style={{
                      backgroundImage:
                        "linear-gradient(rgba(148,163,184,0.18) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.18) 1px, transparent 1px)",
                      backgroundSize: "36px 36px",
                    }}
                  />
                  {[
                    { top: "18%", left: "22%", c: "#ef4444", s: 14 },
                    { top: "62%", left: "38%", c: "#f97316", s: 11 },
                    { top: "35%", left: "62%", c: "#eab308", s: 12 },
                    { top: "70%", left: "72%", c: "#3b82f6", s: 9 },
                    { top: "25%", left: "80%", c: "#22c55e", s: 8 },
                    { top: "55%", left: "14%", c: "#3b82f6", s: 9 },
                    { top: "78%", left: "52%", c: "#ef4444", s: 10 },
                  ].map((p, i) => (
                    <span
                      key={i}
                      className="absolute rounded-full opacity-80"
                      style={{ top: p.top, left: p.left, width: p.s, height: p.s, background: p.c, boxShadow: `0 0 0 4px ${p.c}22` }}
                    />
                  ))}
                  <div className="absolute bottom-2.5 left-2.5 rounded-lg border border-slate-200 bg-white/95 px-2.5 py-1.5 shadow-sm">
                    <p className="text-[9px] font-semibold uppercase tracking-wider text-slate-400">Risk legend</p>
                    <div className="mt-1 flex items-center gap-2">
                      {[["#ef4444", "Critical"], ["#f97316", "High"], ["#eab308", "Elevated"], ["#3b82f6", "Moderate"]].map(([c, l]) => (
                        <span key={l} className="flex items-center gap-1 text-[9px] text-slate-600">
                          <span className="h-1.5 w-1.5 rounded-full" style={{ background: c }} /> {l}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                {/* Stat chips */}
                <div className="mt-3 grid grid-cols-3 gap-3">
                  {[
                    { l: "Active hotspots", v: "378", t: "text-slate-900" },
                    { l: "Critical risk", v: "12", t: "text-red-600" },
                    { l: "Alerts today", v: "29", t: "text-amber-600" },
                  ].map((s) => (
                    <div key={s.l} className="rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2.5">
                      <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">{s.l}</p>
                      <p className={`mt-0.5 font-mono text-xl font-bold ${s.t}`}>{s.v}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Band */}
      <section className="border-b border-slate-100 bg-slate-900">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-x-4 gap-y-8 px-6 py-10 sm:grid-cols-3 lg:grid-cols-6">
          {STATS.map((s, i) => (
            <div key={i} className="text-center">
              <p className="text-2xl font-bold text-white">{s.value}</p>
              <p className="mt-1 text-[10px] font-medium uppercase tracking-wider text-slate-400">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="scroll-mt-16 bg-white py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-14 max-w-2xl">
            <p className="mb-2 text-[12px] font-semibold uppercase tracking-[0.18em] text-accent">Core capabilities</p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              Everything you need for fire intelligence
            </h2>
            <p className="mt-3 text-[15px] leading-relaxed text-slate-600">
              From raw satellite telemetry to explainable decisions — one platform for the full incident lifecycle.
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <div
                key={i}
                className="group rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-sky-50 transition-colors group-hover:bg-sky-100">
                  <f.icon className="h-5 w-5 text-accent" strokeWidth={1.9} />
                </div>
                <h3 className="mb-2 text-[15px] font-semibold text-slate-900">{f.title}</h3>
                <p className="text-[13px] leading-relaxed text-slate-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section id="workflow" className="scroll-mt-16 border-y border-slate-100 bg-slate-50/70 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-14 max-w-2xl">
            <p className="mb-2 text-[12px] font-semibold uppercase tracking-[0.18em] text-accent">How it works</p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
              From satellite pass to response in seconds
            </h2>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {WORKFLOW.map((w) => (
              <div key={w.step} className="relative rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <span className="absolute right-5 top-4 font-mono text-[28px] font-bold text-slate-100">{w.step}</span>
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-accent">
                  <w.icon className="h-5 w-5 text-white" strokeWidth={1.9} />
                </div>
                <h3 className="mb-2 text-[16px] font-semibold text-slate-900">{w.title}</h3>
                <p className="text-[13px] leading-relaxed text-slate-600">{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ML Engine */}
      <section id="ml" className="scroll-mt-16 bg-white py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <p className="mb-2 text-[12px] font-semibold uppercase tracking-[0.18em] text-accent">ML engine</p>
              <h2 className="mb-4 text-3xl font-bold tracking-tight text-slate-900">Why HistGradientBoosting?</h2>
              <p className="mb-6 text-[14px] leading-relaxed text-slate-600">
                We replaced traditional Random Forest — which builds 200+ independent trees using
                brute-force random loops — with scikit-learn&apos;s{" "}
                <strong className="text-slate-900">HistGradientBoostingClassifier</strong>, a
                histogram-based gradient boosting architecture purpose-built for production speed.
              </p>
              <div className="space-y-3">
                {PIPELINE.map((item, i) => (
                  <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                    <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                    <div>
                      <p className="text-[13px] font-semibold text-slate-900">{item.label}</p>
                      <p className="text-[12px] leading-relaxed text-slate-500">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-6">
              <p className="mb-5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                Random Forest vs HistGradientBoosting
              </p>
              <div className="space-y-5">
                {BENCHMARKS.map((row) => (
                  <div key={row.metric}>
                    <div className="mb-1.5 flex items-center justify-between text-[12px]">
                      <span className="font-medium text-slate-700">{row.metric}</span>
                      <span className="font-semibold text-emerald-600">{row.gain}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="w-36 shrink-0 text-[11px] text-slate-500">Random Forest</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
                        <div className="h-full w-full rounded-full bg-slate-400" />
                      </div>
                      <span className="w-14 shrink-0 text-right font-mono text-[11px] text-slate-600">{row.rf}</span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-3">
                      <span className="w-36 shrink-0 text-[11px] font-medium text-accent">HistGradientBoosting</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
                        <div className="h-full rounded-full bg-accent" style={{ width: `${row.hgbPct}%` }} />
                      </div>
                      <span className="w-14 shrink-0 text-right font-mono text-[11px] font-semibold text-accent">{row.hgb}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section id="tech" className="scroll-mt-16 border-y border-slate-100 bg-slate-50/70 py-20">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="mb-8 text-2xl font-bold tracking-tight text-slate-900">Built with modern technology</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {TECH.map((t, i) => (
              <span
                key={i}
                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-[12px] font-medium text-slate-600 shadow-sm transition-colors hover:border-sky-200 hover:text-accent"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA banner */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-sky-600 via-sky-600 to-cyan-600 px-8 py-12 text-center shadow-lg shadow-sky-600/20">
            <h2 className="mb-3 text-3xl font-bold tracking-tight text-white">Ready to detect faster?</h2>
            <p className="mx-auto mb-8 max-w-xl text-[14px] leading-relaxed text-sky-100">
              Join FIRE-X and get access to real-time fire intelligence powered by NASA satellites and AI.
            </p>
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-7 py-3.5 text-[14px] font-semibold text-sky-700 shadow-sm transition-colors hover:bg-sky-50"
            >
              Create free account <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 py-12 sm:grid-cols-3">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <Flame className="h-4 w-4 text-accent" fill="currentColor" />
              <span className="text-[13px] font-semibold tracking-wider text-slate-900">FIRE-X</span>
            </div>
            <p className="max-w-xs text-[12px] leading-relaxed text-slate-500">
              AI-enabled geospatial fire intelligence platform. Detect. Classify. Understand. Respond.
            </p>
          </div>
          <div>
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-900">Platform</p>
            <div className="flex flex-col gap-2 text-[12px] text-slate-500">
              <a href="#features" className="hover:text-accent">Features</a>
              <a href="#workflow" className="hover:text-accent">How it works</a>
              <a href="#ml" className="hover:text-accent">ML engine</a>
            </div>
          </div>
          <div>
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-900">Program</p>
            <div className="flex flex-col gap-2 text-[12px] text-slate-500">
              <span>Smart India Hackathon 2026</span>
              <span>PS 26162 · NTRO</span>
              <span>Disaster Management</span>
            </div>
          </div>
        </div>
        <div className="border-t border-slate-100 py-5">
          <p className="text-center text-[11px] text-slate-400">© 2026 Team Pragya-X · Powered by NASA FIRMS · Scikit-learn · FastAPI · Next.js</p>
        </div>
      </footer>
    </div>
  );
}
