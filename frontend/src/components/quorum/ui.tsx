import { cn } from "@/lib/utils";
import { STEPS } from "@/lib/session-store";
import { Check } from "lucide-react";
import type { ReactNode } from "react";
import type { Message } from "@/lib/mock-data";
import { MARKET_INFO, isVisible } from "@/lib/mock-data";
import { ActionBadge, MarketBadge, MsgTypeBadge, VisibilityTag } from "./badges";

export function PageHeader({ eyebrow, title, desc, actions }: { eyebrow?: string; title: string; desc?: string; actions?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && <p className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">{eyebrow}</p>}
        <h1 className="text-3xl font-semibold">{title}</h1>
        {desc && <p className="mt-2 max-w-2xl text-muted-foreground">{desc}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Panel({ title, children, className, action }: { title?: string; children: ReactNode; className?: string; action?: ReactNode }) {
  return (
    <section className={cn("rounded-xl border border-border bg-card p-5 shadow-soft", className)}>
      {title && (
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">{title}</h2>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Kpi({ label, value, tone }: { label: string; value: string; tone?: "buy" | "sell" }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={cn("mt-2 font-display text-3xl font-semibold", tone === "buy" && "text-buy", tone === "sell" && "text-sell")}>{value}</p>
    </div>
  );
}

export function Stepper({ current, done, turns }: { current: number; done: boolean; turns?: number }) {
  return (
    <ol className="space-y-1">
      {STEPS.map((s, i) => {
        const complete = done || i < current;
        const active = !done && i === current;
        return (
          <li key={s} className={cn("flex items-center gap-3 rounded-lg px-2 py-1.5 transition-colors", active && "bg-primary-soft")}>
            <span
              className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
                complete && "border-primary bg-primary text-primary-foreground",
                active && "animate-pulse-ring border-primary text-primary",
                !complete && !active && "border-border text-muted-foreground",
              )}
            >
              {complete ? <Check className="h-3.5 w-3.5" /> : i + 1}
            </span>
            <span className={cn("text-sm", active ? "font-semibold text-foreground" : complete ? "text-foreground" : "text-muted-foreground")}>
              {s}
              {i === 3 && turns !== undefined && <span className="ml-1 font-mono text-xs text-muted-foreground">({turns}/3 turns)</span>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export function MessageBubble({ msg, active, onClick }: { msg: Message; active?: boolean; onClick?: () => void }) {
  const vis = isVisible(msg);
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "animate-rise w-full rounded-xl border bg-card p-4 text-left transition-all hover:border-primary/40",
        active ? "border-primary ring-2 ring-primary/20" : "border-border",
        !vis && "bg-muted/60",
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <MarketBadge market={msg.from} />
        <span className="text-xs text-muted-foreground">→ {msg.to === "BOARD" ? "Board" : msg.to}</span>
        <MsgTypeBadge type={msg.type} />
        <span className="ml-auto"><ActionBadge action={msg.position} /></span>
      </div>
      <p className="mt-2.5 text-sm leading-relaxed">{msg.reason}</p>
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {msg.evidence.map((e) => (
          <span key={e} className="rounded border border-border px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">{e}</span>
        ))}
        <span className="ml-auto"><VisibilityTag visible={vis} /></span>
      </div>
    </button>
  );
}

export function SupervisorEvent({ text }: { text: string }) {
  return (
    <div className="animate-rise flex items-center gap-3 py-1 text-xs text-muted-foreground">
      <span className="h-px flex-1 bg-border" />
      <span className="rounded-full bg-secondary px-3 py-1 font-medium">Supervisor · {text}</span>
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

export function EmptyState({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border p-10 text-center">
      <p className="font-display font-semibold">{title}</p>
      <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
    </div>
  );
}

export const marketOpen = (m: keyof typeof MARKET_INFO) => MARKET_INFO[m].open;
