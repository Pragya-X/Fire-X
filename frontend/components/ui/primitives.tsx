"use client";

import React, { forwardRef, useEffect, useState } from "react";
import { X } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/* ---------------------------------- Button ---------------------------------- */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 disabled:pointer-events-none disabled:opacity-50 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-accent text-white hover:bg-accent/90",
        secondary: "bg-base text-secondary border border-base-border hover:bg-base-panel",
        ghost: "text-muted hover:bg-base-raised hover:text-primary",
        outline: "border border-base-border bg-base text-secondary hover:bg-base-panel",
        danger: "bg-critical text-white hover:bg-critical/90",
        success: "bg-low text-white border border-low/40 hover:bg-low/80",
        link: "text-accent underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
);
Button.displayName = "Button";

/* ----------------------------------- Card ----------------------------------- */
export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("rounded-lg border border-base-border bg-base shadow-sm", className)} {...props} >
      {children}
    </div>
  );
}

export function CardHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("flex items-center justify-between gap-3 border-b border-base-border/70 px-4 py-3", className)}>{children}</div>;
}

export function CardTitle({ className, children }: { className?: string; children: React.ReactNode }) {
  return <h3 className={cn("text-sm font-semibold tracking-wide text-primary", className)}>{children}</h3>;
}

export function CardBody({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("p-4", className)}>{children}</div>;
}

/* ---------------------------------- Badge ----------------------------------- */
export type BadgeTone = "critical" | "high" | "moderate" | "low" | "info" | "muted" | "purple";
const toneClass: Record<BadgeTone, string> = {
  critical: "bg-red-50 text-red-700 border-red-300",
  high: "bg-orange-50 text-orange-700 border-orange-300",
  moderate: "bg-amber-50 text-amber-700 border-amber-300",
  low: "bg-green-50 text-green-700 border-green-300",
  info: "bg-blue-50 text-blue-700 border-blue-300",
  muted: "bg-base-panel text-muted border-base-border",
  purple: "bg-purple-50 text-purple-700 border-purple-300",
};

export function Badge({ tone = "muted", className, children, icon }: { tone?: BadgeTone; className?: string; children: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-[11px] font-medium tracking-wide", toneClass[tone], className)}>
      {icon}
      {children}
    </span>
  );
}

/* ---------------------------------- Input ----------------------------------- */
export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn("h-9 w-full rounded-md border border-base-border bg-base px-3 text-sm text-primary placeholder:text-muted focus:border-accent/60 focus:outline-none focus:ring-1 focus:ring-accent/40 disabled:opacity-50", className)}
      {...props}
    />
  )
);
Input.displayName = "Input";

/* ---------------------------------- Select ---------------------------------- */
export function Select({ className, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn("h-9 w-full appearance-none rounded-md border border-base-border bg-base px-3 text-sm text-primary focus:border-accent/60 focus:outline-none focus:ring-1 focus:ring-accent/40", className)} {...props}>
      {children}
    </select>
  );
}

/* ---------------------------------- Textarea --------------------------------- */
export const Textarea = forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea ref={ref} className={cn("w-full rounded-md border border-base-border bg-base px-3 py-2 text-sm text-primary placeholder:text-muted focus:border-accent/60 focus:outline-none focus:ring-1 focus:ring-accent/40", className)} {...props} />
  )
);
Textarea.displayName = "Textarea";

/* ---------------------------------- Dialog ---------------------------------- */
export function Dialog({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title?: string; children: React.ReactNode; wide?: boolean }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 pt-16" onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div className={cn("w-full animate-fadeIn rounded-lg border border-base-border bg-base shadow-sm", wide ? "max-w-4xl" : "max-w-2xl")} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-base-border/70 px-5 py-3">
          <h3 className="text-sm font-semibold text-primary">{title}</h3>
          <button onClick={onClose} className="rounded p-1 text-muted hover:bg-base-raised hover:text-primary" aria-label="Close dialog">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

/* ---------------------------------- Skeleton --------------------------------- */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded bg-base-raised", className)} />;
}

/* ---------------------------------- Empty / Error --------------------------------- */
export function EmptyState({ title, message }: { title: string; message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      <p className="text-sm font-medium text-muted">{title}</p>
      {message && <p className="max-w-sm text-xs text-muted/70">{message}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-red-300 bg-red-50/50 py-10 text-center">
      <p className="text-sm text-red-600">{message}</p>
      {onRetry && <Button variant="outline" size="sm" onClick={onRetry}>Retry</Button>}
    </div>
  );
}

/* ---------------------------------- Toast ---------------------------------- */
export interface ToastItem {
  id: number;
  title: string;
  message?: string;
  tone: "info" | "success" | "error" | "critical";
}

export const ToastContext = React.createContext<{ push: (t: Omit<ToastItem, "id">) => void }>({ push: () => undefined });

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const push = React.useCallback((t: Omit<ToastItem, "id">) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { ...t, id }]);
    setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== id)), 5000);
  }, []);
  const toneClass: Record<ToastItem["tone"], string> = {
    info: "border-blue-300",
    success: "border-green-300",
    error: "border-red-300",
    critical: "border-red-500",
  };
  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[90] flex w-80 flex-col gap-2" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={cn("animate-fadeIn rounded-lg border bg-base p-3 shadow-sm", toneClass[t.tone])}>
            <p className="text-xs font-semibold text-primary">{t.title}</p>
            {t.message && <p className="mt-0.5 text-xs text-muted">{t.message}</p>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return React.useContext(ToastContext);
}

/* ---------------------------------- Tabs ---------------------------------- */
export function Tabs({ tabs, active, onChange }: { tabs: { id: string; label: string }[]; active: string; onChange: (id: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1 rounded-md border border-base-border bg-base-panel p-1" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={active === t.id} onClick={() => onChange(t.id)} className={cn("rounded px-3 py-1.5 text-xs font-medium transition-colors", active === t.id ? "bg-base text-primary shadow-sm" : "text-muted hover:text-primary")}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ---------------------------------- Table --------------------------------- */
export function Table({ className, children, ...props }: React.TableHTMLAttributes<HTMLTableElement>) {
  return <table className={cn("w-full border-collapse text-sm", className)} {...props}>{children}</table>;
}

export function TableHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <thead className={cn("border-b border-base-border bg-base-panel", className)}>{children}</thead>;
}

export function TableRow({ className, children, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={cn("border-b border-base-border/40 hover:bg-base-panel transition-colors", className)} {...props} />;
}

export function TableCell({ className, children, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn("px-3 py-2 text-secondary", className)} {...props} />;
}

export function TableHead({ className, children, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return <th className={cn("px-3 py-2 text-left text-xs font-medium text-muted", className)} {...props} />;
}
