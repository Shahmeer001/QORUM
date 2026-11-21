import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Pause, Play, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ActionBadge, MarketBadge, MsgTypeBadge, VisibilityTag } from "@/components/quorum/badges";
import { EmptyState, MessageBubble, PageHeader, Panel } from "@/components/quorum/ui";
import { isVisible, type Action, type Message } from "@/lib/mock-data";
import { useSession } from "@/lib/session-store";

export const Route = createFileRoute("/replay")({
  head: () => ({
    meta: [
      { title: "Message Replay — QUORUM" },
      { name: "description", content: "Replay every typed debate message round by round from the API." },
      { property: "og:title", content: "Message Replay — QUORUM" },
      { property: "og:description", content: "Replay every typed debate message round by round." },
    ],
  }),
  component: Replay,
});

function Replay() {
  const { sessionData } = useSession();
  const messages = sessionData.messages || [];

  const [round, setRound] = useState("all");
  const [type, setType] = useState("all");
  const [market, setMarket] = useState("all");
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [detail, setDetail] = useState<Message | null>(null);

  const list = useMemo(
    () => messages.filter((m) =>
      (round === "all" || m.round === +round) &&
      (type === "all" || m.type === type) &&
      (market === "all" || m.from === market) &&
      (!q || m.reason.toLowerCase().includes(q.toLowerCase()))),
    [messages, round, type, market, q],
  );

  useEffect(() => setIdx(0), [list]);
  useEffect(() => {
    if (!playing) return;
    if (idx >= list.length - 1) { setPlaying(false); return; }
    const t = setTimeout(() => setIdx((i) => i + 1), 1400 / speed);
    return () => clearTimeout(t);
  }, [playing, idx, list.length, speed]);

  const active = list[idx];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={`Session ${sessionData.id}`}
        title="Message Replay"
        desc="Audit and replay every typed debate message from the decision session."
      />
      <div className="flex flex-wrap gap-3 rounded-xl border border-border bg-card p-4 shadow-soft">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => setPlaying(!playing)}>
            {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button size="sm" variant="outline" disabled={idx <= 0} onClick={() => setIdx((i) => Math.max(0, i - 1))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="font-mono text-sm">{list.length ? `${idx + 1} / ${list.length}` : "0"}</span>
          <Button size="sm" variant="outline" disabled={idx >= list.length - 1} onClick={() => setIdx((i) => Math.min(list.length - 1, i + 1))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        <div className="relative min-w-[200px] flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Filter by text or evidence..." value={q} onChange={(e) => setQ(e.target.value)} className="pl-9" />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <Panel title="Message Feed">
          <div className="space-y-3">
            {list.map((m, i) => (
              <div
                key={m.id}
                onClick={() => setIdx(i)}
                className={`cursor-pointer rounded-lg border p-3 transition-colors ${
                  i === idx ? "border-primary bg-primary-soft/30" : "border-border hover:bg-muted/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MarketBadge market={m.from} />
                    <span className="text-xs text-muted-foreground">→</span>
                    <span className="font-mono text-xs">{m.to}</span>
                    <MsgTypeBadge type={m.type} />
                  </div>
                  <ActionBadge action={m.position} />
                </div>
                <p className="mt-2 text-sm">{m.reason}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Active Message Inspection">
          {active ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">From Market</p>
                <p className="mt-1 font-display text-lg font-semibold">{active.from}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Position & Confidence</p>
                <div className="mt-1 flex items-center gap-2">
                  <ActionBadge action={active.position} size="lg" />
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Reasoning</p>
                <p className="mt-1 text-sm leading-relaxed">{active.reason}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Evidence Tags</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {active.evidence.map((e) => (
                    <span key={e} className="rounded border border-border px-2 py-0.5 font-mono text-xs">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <EmptyState title="No message selected" desc="Select a message to view detail." />
          )}
        </Panel>
      </div>
    </div>
  );
}
