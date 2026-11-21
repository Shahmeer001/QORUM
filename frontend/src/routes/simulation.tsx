import { createFileRoute } from "@tanstack/react-router";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ActionBadge, MarketBadge } from "@/components/quorum/badges";
import { Kpi, PageHeader, Panel } from "@/components/quorum/ui";
import { type Action, type Market } from "@/lib/mock-data";
import { useSession } from "@/lib/session-store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/simulation")({
  head: () => ({
    meta: [
      { title: "Simulation & Metrics — QUORUM" },
      { name: "description", content: "Simulated PnL, drawdown, win rate and trade log from the backend API." },
      { property: "og:title", content: "Simulation & Metrics — QUORUM" },
      { property: "og:description", content: "Simulated PnL, drawdown, win rate and trade log." },
    ],
  }),
  component: Simulation,
});

function Simulation() {
  const { sessionData } = useSession();
  const s = sessionData;

  const equityData = s.equity?.length ? s.equity : [{ t: "D1", v: 10000 }];
  const tradesData = s.trades || [];
  const riskEvents = s.risk_events || [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={`Session ${s.id}`}
        title="Simulation & Metrics"
        desc={`How the strategy performed on ${s.asset} (${s.target}) in ${s.mode.toUpperCase()} mode.`}
      />
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <Kpi label="Simulated PnL" value={`+${s.pnl.toFixed(2)}%`} tone="buy" />
        <Kpi label="Max drawdown" value={`−${s.max_drawdown.toFixed(2)}%`} tone="sell" />
        <Kpi label="Win rate" value={`${s.win_rate.toFixed(0)}%`} />
        <Kpi label="Final Action" value={s.final_action} />
        <Kpi label="Trades" value={String(tradesData.length)} />
      </div>

      <Panel title="Equity curve ($)">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={equityData} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis dataKey="t" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis domain={["dataMin - 50", "dataMax + 50"]} stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} width={56} />
              <Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8 }} />
              <Line type="monotone" dataKey="v" name="Equity ($)" stroke="var(--primary)" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Panel title="Trades Log">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entry</TableHead>
                <TableHead>Exit</TableHead>
                <TableHead>Side</TableHead>
                <TableHead>Market</TableHead>
                <TableHead className="text-right">PnL</TableHead>
                <TableHead>Notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tradesData.map((t, idx) => (
                <TableRow key={`${t.entry}-${idx}`}>
                  <TableCell className="font-mono text-xs">{t.entry}</TableCell>
                  <TableCell className="font-mono text-xs">{t.exit}</TableCell>
                  <TableCell><ActionBadge action={t.side} /></TableCell>
                  <TableCell><MarketBadge market={t.market} /></TableCell>
                  <TableCell className={cn("text-right font-mono", t.pnl > 0 ? "text-buy" : t.pnl < 0 ? "text-sell" : "text-muted-foreground")}>
                    {t.pnl > 0 ? "+" : ""}{t.pnl ? `$${t.pnl}` : "—"}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{t.note}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Panel>

        <Panel title="Risk Events">
          <div className="space-y-3">
            {riskEvents.map((e, idx) => (
              <div key={idx} className="rounded-lg border border-border p-3 text-sm">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-mono">{e.time}</span>
                  <span className={cn("font-medium uppercase", e.level === "override" ? "text-hold" : e.level === "warn" ? "text-yellow-500" : "text-buy")}>
                    {e.level}
                  </span>
                </div>
                <p className="mt-1">{e.text}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
