import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowRight, Eye, GitBranch, History, LineChart, MessagesSquare, ShieldCheck, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ActionBadge, MarketBadge } from "@/components/quorum/badges";
import { Panel } from "@/components/quorum/ui";
import { MARKETS } from "@/lib/mock-data";
import { fetchLatestSession, type SessionResultData } from "@/lib/api";
import { useSession } from "@/lib/session-store";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "QUORUM — Cross-Market Multi-Agent Decisions" },
      { name: "description", content: "Five market agents debate, a supervisor forms consensus, and risk control has the final say." },
      { property: "og:title", content: "QUORUM — Cross-Market Multi-Agent Decisions" },
      { property: "og:description", content: "Five market agents debate, a supervisor forms consensus, and risk control has the final say." },
    ],
  }),
  component: Overview,
});

const FLOW = ["Configure", "Fetch Data", "Agent Analysis", "Debate (max 3 turns)", "Decision + Risk + Simulation"];
const CAPS = [
  { icon: Users, t: "Multi-agent recommendations", d: "One analyst agent per market." },
  { icon: MessagesSquare, t: "Typed debate messages", d: "Recommend, Challenge, Reply, Final." },
  { icon: Eye, t: "Closed-market visibility", d: "Only closed-market messages are shared." },
  { icon: ShieldCheck, t: "Risk override", d: "Risk control can force HOLD or ABSTAIN." },
  { icon: History, t: "Replayable message log", d: "Step through every debate round." },
  { icon: LineChart, t: "Simulation metrics", d: "PnL, drawdown, win rate and more." },
];

function Overview() {
  const { sessionData, setSessionData } = useSession();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let unmounted = false;
    fetchLatestSession().then((data) => {
      if (!unmounted && data) setSessionData(data);
    });
    return () => { unmounted = true; };
  }, [setSessionData]);

  const s = sessionData;

  return (
    <div className="space-y-10">
      <section className="animate-rise relative overflow-hidden rounded-2xl border border-border bg-card px-8 py-12 shadow-soft md:px-12">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary-soft" />
        <div className="relative max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Final Year Project</p>
          <h1 className="mt-3 text-6xl font-bold tracking-[0.06em] md:text-7xl">QUORUM</h1>
          <p className="mt-4 text-xl text-muted-foreground">Cross-market multi-agent decisions with supervised debate.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button size="lg" asChild>
              <Link to="/new-session">Start Decision Session <ArrowRight className="h-4 w-4" /></Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/results">View Latest Result</Link>
            </Button>
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-2">
            <span className="mr-1 text-xs text-muted-foreground">Markets covered</span>
            {MARKETS.map((m) => <MarketBadge key={m} market={m} className="px-3 py-1 text-sm" />)}
          </div>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold">How QUORUM works</h2>
        <div className="grid gap-3 md:grid-cols-5">
          {FLOW.map((f, i) => (
            <div key={f} className="relative rounded-xl border border-border bg-card p-4">
              <span className="font-mono text-xs text-primary">0{i + 1}</span>
              <p className="mt-1 font-display font-semibold leading-snug">{f}</p>
              {i < FLOW.length - 1 && <ArrowRight className="absolute -right-2.5 top-1/2 z-10 hidden h-4 w-4 -translate-y-1/2 text-muted-foreground md:block" />}
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <section>
          <h2 className="mb-4 text-xl font-semibold">Key capabilities</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {CAPS.map(({ icon: Icon, t, d }) => (
              <div key={t} className="flex gap-3 rounded-xl border border-border bg-card p-4">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                <div>
                  <p className="font-semibold">{t}</p>
                  <p className="text-sm text-muted-foreground">{d}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
        <Panel title="Latest session summary" className="self-start" action={<GitBranch className="h-4 w-4 text-muted-foreground" />}>
          <dl className="space-y-3 text-sm">
            <Row k="Session ID" v={<span className="font-mono font-semibold">{s.id}</span>} />
            <Row k="Target asset" v={<span className="font-mono">{s.asset} ({s.target})</span>} />
            <Row k="Mode" v={<span className="font-mono capitalize">{s.mode}</span>} />
            <Row k="Final action" v={<ActionBadge action={s.final_action} size="lg" />} />
            <Row k="Turns used" v={`${s.turns_used}/${s.max_turns}`} />
            <Row k="Risk status" v={<span className="font-medium text-hold">{s.risk_status}</span>} />
            <Row k="Simulated PnL" v={<span className="font-mono font-semibold text-buy">+{s.pnl.toFixed(2)}%</span>} />
          </dl>
          <Button className="mt-5 w-full" variant="outline" asChild>
            <Link to="/results">Open Result</Link>
          </Button>
        </Panel>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
      <dt className="text-muted-foreground">{k}</dt>
      <dd>{v}</dd>
    </div>
  );
}
