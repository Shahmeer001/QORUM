import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/quorum/ui";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About QUORUM — Final Year Project" },
      { name: "description", content: "The problem, solution and design behind QUORUM's multi-agent decision system." },
      { property: "og:title", content: "About QUORUM — Final Year Project" },
      { property: "og:description", content: "The problem, solution and design behind QUORUM." },
    ],
  }),
  component: About,
});

const SECTIONS = [
  { t: "Problem", d: "Markets are connected, but most tools analyse one market at a time. Single-model signals miss cross-market context and can be overconfident." },
  { t: "Solution", d: "QUORUM assigns one agent per market. Agents recommend, debate, and a supervisor forms a consensus that risk control can veto." },
  { t: "Why multi-agent debate", d: "Debate exposes weak arguments. Agents must reply to challenges, so the final decision is tested from several angles." },
  { t: "Closed-market rule", d: "Only closed-market messages are shared — open markets are still moving, so their views could leak unstable information." },
  { t: "Risk layer", d: "Even a strong consensus can be overridden to HOLD or ABSTAIN when volatility, drawdown or stop-loss limits are breached." },
  { t: "What this UI shows", d: "Configuration, live agent debate, typed messages, consensus, risk override, trade simulation and full message replay." },
];

function About() {
  return (
    <div>
      <PageHeader eyebrow="Final Year Project" title="About QUORUM" desc="Cross-Market Multi-Agent Consensus for Smarter Decisions." />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {SECTIONS.map((s, i) => (
          <section key={s.t} className="rounded-xl border border-border bg-card p-6 shadow-soft">
            <span className="font-mono text-sm text-primary">0{i + 1}</span>
            <h2 className="mt-2 text-xl font-semibold">{s.t}</h2>
            <p className="mt-2 leading-relaxed text-muted-foreground">{s.d}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
