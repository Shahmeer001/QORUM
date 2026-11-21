import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ActionBadge, MarketBadge, RoleBadge } from "@/components/quorum/badges";
import { PageHeader, Panel } from "@/components/quorum/ui";
import { MARKETS } from "@/lib/mock-data";
import { useSession } from "@/lib/session-store";

export const Route = createFileRoute("/results")({
  head: () => ({
    meta: [
      { title: "Decision Result — QUORUM" },
      { name: "description", content: "Final action, agent positions and the reasoning behind QUORUM's decision from API." },
      { property: "og:title", content: "Decision Result — QUORUM" },
      { property: "og:description", content: "Final action, agent positions and reasoning." },
    ],
  }),
  component: Results,
});

function Results() {
  const { sessionData } = useSession();
  const s = sessionData;

  return (
    <div className="space-y-6">
      <PageHeader eyebrow={`Session ${s.id}`} title="Decision Result" />
      <section className="animate-rise grid gap-6 rounded-2xl border border-border bg-card p-8 shadow-soft md:grid-cols-[auto_1fr]">
        <div className="flex flex-col items-center justify-center gap-2 border-border md:border-r md:pr-10">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Final action</span>
          <ActionBadge action={s.final_action} size="xl" />
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <Stat k="Asset" v={<span className="font-mono">{s.asset}</span>} />
          <Stat k="Mode" v={<span className="font-mono capitalize">{s.mode}</span>} />
          <Stat k="Turns used" v={`${s.turns_used} / ${s.max_turns}`} />
          <Stat k="Timestamp" v={s.timestamp} />
          <Stat k="Target market" v={<MarketBadge market={s.target} />} />
          <Stat k="Risk status" v={<span className="font-medium text-hold">{s.risk_status}</span>} />
          <div className="flex items-start gap-3 rounded-xl bg-hold-soft p-4 sm:col-span-2 lg:col-span-4">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-hold" />
            <div className="text-sm">
              <p className="font-semibold">Risk control: {s.risk_status} (Consensus: <ActionBadge action={s.consensus} /> → Final: <ActionBadge action={s.final_action} />)</p>
              <p className="mt-1 text-muted-foreground">{s.risk_note}</p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Final recommendation summary">
          <ul className="space-y-2 text-sm">
            {s.agents.map((a) => (
              <li key={a.market} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span>
                  <strong>{a.market}</strong> ({a.final}): {a.reason}
                </span>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Why this decision">
          <p className="leading-relaxed">
            The supervisor aggregated weighted stances across the active market agents.
            The consensus was <strong>{s.consensus}</strong>.
            The risk management layer evaluated market volatility and stop thresholds, resulting in a final execution directive of <strong>{s.final_action}</strong>.
          </p>
          <div className="mt-4 flex gap-3">
            <Button asChild>
              <Link to="/simulation">View Simulation & Metrics <ArrowRight className="h-4 w-4" /></Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/replay">Replay Debate Messages</Link>
            </Button>
          </div>
        </Panel>
      </div>

      <Panel title="Agent positions summary">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Market</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Initial</TableHead>
              <TableHead>Final</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Summary Reasoning</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {s.agents.map((a) => (
              <TableRow key={a.market}>
                <TableCell><MarketBadge market={a.market} /></TableCell>
                <TableCell><RoleBadge role={a.role} /></TableCell>
                <TableCell><ActionBadge action={a.initial} /></TableCell>
                <TableCell><ActionBadge action={a.final} /></TableCell>
                <TableCell className="font-mono">{a.confidence}%</TableCell>
                <TableCell className="text-sm text-muted-foreground">{a.reason}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Panel>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider text-muted-foreground">{k}</p>
      <div className="mt-1">{v}</div>
    </div>
  );
}
