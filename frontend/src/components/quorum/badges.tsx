import { cn } from "@/lib/utils";
import type { Action, Market, MsgType, Role } from "@/lib/mock-data";
import type { SessionStatus } from "@/lib/session-store";
import { Eye, EyeOff } from "lucide-react";

const actionStyles: Record<Action, string> = {
  BUY: "bg-buy-soft text-buy border-buy/30",
  SELL: "bg-sell-soft text-sell border-sell/30",
  HOLD: "bg-hold-soft text-hold border-hold/30",
  ABSTAIN: "bg-abstain-soft text-abstain border-abstain/30",
};

export function ActionBadge({ action, size = "sm" }: { action: Action; size?: "sm" | "lg" | "xl" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-md border font-mono font-semibold tracking-wide",
        actionStyles[action],
        size === "sm" && "px-2 py-0.5 text-xs",
        size === "lg" && "px-3 py-1 text-sm",
        size === "xl" && "px-6 py-3 text-3xl",
      )}
    >
      {action}
    </span>
  );
}

export function MarketBadge({ market, className }: { market: Market; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-md bg-secondary px-2 py-0.5 font-mono text-xs font-semibold text-secondary-foreground", className)}>
      {market}
    </span>
  );
}

export function RoleBadge({ role }: { role: Role }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wider",
        role === "CHOSEN" ? "bg-primary text-primary-foreground" : "border border-border text-muted-foreground",
      )}
    >
      {role}
    </span>
  );
}

const typeStyles: Record<MsgType, string> = {
  RECOMMEND: "bg-primary-soft text-primary",
  CHALLENGE: "bg-sell-soft text-sell",
  REPLY: "bg-secondary text-secondary-foreground",
  FINAL: "bg-foreground text-background",
};

export function MsgTypeBadge({ type }: { type: MsgType }) {
  return <span className={cn("rounded px-1.5 py-0.5 font-mono text-[10px] font-bold tracking-wider", typeStyles[type])}>{type}</span>;
}

export function VisibilityTag({ visible }: { visible: boolean }) {
  return visible ? (
    <span className="inline-flex items-center gap-1 text-xs text-buy">
      <Eye className="h-3 w-3" /> Visible
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
      <EyeOff className="h-3 w-3" /> Hidden (open-market rule)
    </span>
  );
}

export function StatusChip({ status }: { status: SessionStatus }) {
  const dot = {
    Idle: "bg-abstain",
    Running: "bg-primary animate-pulse",
    Debating: "bg-hold animate-pulse",
    Completed: "bg-buy",
  }[status];
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium">
      <span className={cn("h-2 w-2 rounded-full", dot)} />
      {status}
    </span>
  );
}

export function OpenClosed({ open }: { open: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", open ? "text-buy" : "text-muted-foreground")}>
      <span className={cn("h-1.5 w-1.5 rounded-full", open ? "bg-buy" : "bg-abstain")} />
      {open ? "Open" : "Closed"}
    </span>
  );
}
