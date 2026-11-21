import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ChevronDown, Pause, Play, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ActionBadge, MarketBadge, OpenClosed, RoleBadge } from "@/components/quorum/badges";
import { MessageBubble, PageHeader, Panel, Stepper, SupervisorEvent } from "@/components/quorum/ui";
import { MARKET_INFO, type Action, type Message } from "@/lib/mock-data";
import { TOTAL_TICKS, tickToRound, tickToStep, useSession } from "@/lib/session-store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/live")({
  head: () => ({
    meta: [
      { title: "Live Session — QUORUM" },
      { name: "description", content: "Watch market agents recommend, debate and reach consensus in real time." },
      { property: "og:title", content: "Live Session — QUORUM" },
      { property: "og:description", content: "Watch market agents recommend, debate and reach consensus." },
    ],
  }),
  component: Live,
});

function Live() {
  const { tick, playing, start, togglePause, status, sessionData } = useSession();
  const [tab, setTab] = useState(0);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    if (status === "Idle") start();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const round = tickToRound(tick);
  const step = tickToStep(tick);
  const done = tick >= TOTAL_TICKS;
  const turns = Math.max(0, round);

  useEffect(() => {
    if (round >= 0) setTab(round);
  }, [round]);

  const msgs = sessionData.messages || [];
  const agents = sessionData.agents || [];

  const positionAt = (market: string): Action | null => {
    const mList = msgs.filter((m) => m.from === market && m.round <= round);
    return mList.at(-1)?.position ?? null;
  };

  const shown = msgs.filter((m) => m.round === tab && m.round <= round);
  const current = round >= 0 ? agents.map((a) => positionAt(a.market)) : [];
  const disagree = new Set(current.filter(Boolean)).size > 1;

  return (
    <div>
      <PageHeader
        eyebrow={`Session ${sessionData.id} · ${sessionData.asset}`}
        title="Live Session"
        desc={`Mode: ${sessionData.mode.toUpperCase()} · Five market agents analyse, debate and converge. The supervisor moderates; risk control has the last word.`}
        actions={<Button variant="outline" onClick={() => start()}><RotateCcw className="h-4 w-4" /> Replay Demo</Button>}
      />
      <div className="grid gap-6 xl:grid-cols-[300px_1fr_280px]">
        {/* Agents */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Market agents</h2>
          {agents.map((a) => {
            const pos = positionAt(a.market);
            const info = MARKET_INFO[a.market as keyof typeof MARKET_INFO] || { open: false };
            return (
              <div key={a.market} className="rounded-xl border border-border bg-card p-4 shadow-soft">
                <div className="flex items-center gap-2">
                  <span className="font-display font-semibold">{a.market}</span>
                  <RoleBadge role={a.role} />
                  <span className="ml-auto"><OpenClosed open={info.open} /></span>
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Stance</span>
                  {pos ? <ActionBadge action={pos} /> : <span className="font-mono text-xs text-muted-foreground">Analyzing...</span>}
                </div>
                <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{a.reason}</p>
              </div>
            );
          })}
        </div>

        {/* Center: Message board */}
        <div className="space-y-4">
          <Stepper currentStep={step} />
          <Panel
            title={`Debate Board — Round ${tab}`}
            action={
              <div className="flex gap-1">
                {[0, 1, 2].map((r) => (
                  <Button key={r} size="sm" variant={tab === r ? "default" : "outline"} onClick={() => setTab(r)}>
                    Round {r}
                  </Button>
                ))}
              </div>
            }
          >
            <div className="space-y-3">
              {shown.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">No messages for this round yet.</p>
              ) : (
                shown.map((m) => (
                  <MessageBubble
                    key={m.id}
                    msg={m}
                    isOpen={open === m.id}
                    onToggle={() => setOpen((o) => (o === m.id ? null : m.id))}
                  />
                ))
              )}
            </div>
          </Panel>
        </div>

        {/* Right: Supervisor / Consensus */}
        <div className="space-y-4">
          <Panel title="Supervisor Status">
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-muted-foreground">Debate round</dt>
                <dd className="font-mono font-medium">{round < 0 ? "Pending" : round}</dd>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-muted-foreground">Turns used</dt>
                <dd className="font-mono font-medium">{turns} / {sessionData.max_turns}</dd>
              </div>
              <div className="flex justify-between border-b border-border pb-2">
                <dt className="text-muted-foreground">Current stance</dt>
                <dd><ActionBadge action={sessionData.consensus} /></dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Agreement</dt>
                <dd className={cn("font-medium", disagree ? "text-sell" : "text-buy")}>
                  {disagree ? "Disagreement" : "Convergence"}
                </dd>
              </div>
            </dl>
            <div className="mt-4 flex gap-2">
              <Button className="w-full" variant="outline" onClick={togglePause}>
                {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {playing ? "Pause" : "Play"}
              </Button>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
