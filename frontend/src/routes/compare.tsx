import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ActionBadge, MarketBadge } from "@/components/quorum/badges";
import { EmptyState, PageHeader } from "@/components/quorum/ui";
import { fetchCompareSetups } from "@/lib/api";
import { COMPARE_SETUPS, type CompareSetup, type Market } from "@/lib/mock-data";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare Setups — QUORUM" },
      { name: "description", content: "Compare Single, Silent, and Debate modes side-by-side from the API." },
      { property: "og:title", content: "Compare Setups — QUORUM" },
      { property: "og:description", content: "Compare QUORUM sessions side by side." },
    ],
  }),
  component: Compare,
});

const ROWS: { k: string; render: (s: CompareSetup) => React.ReactNode; best?: (s: CompareSetup[]) => string }[] = [
  { k: "Markets selected", render: (s) => <div className="flex flex-wrap gap-1">{s.markets.map((m) => <MarketBadge key={m} market={m as Market} />)}</div> },
  { k: "Final action", render: (s) => <ActionBadge action={s.action} /> },
  { k: "Turns used", render: (s) => `${s.turns} / 3` },
  { k: "Risk override", render: (s) => (s.override ? <span className="font-medium text-hold">Yes</span> : "No") },
  { k: "Simulated PnL", render: (s) => <span className="font-mono">+{s.pnl.toFixed(2)}%</span>, best: (l) => l.reduce((a, b) => (b.pnl > a.pnl ? b : a)).id },
  { k: "Max drawdown", render: (s) => <span className="font-mono">−{s.drawdown.toFixed(1)}%</span>, best: (l) => l.reduce((a, b) => (b.drawdown < a.drawdown ? b : a)).id },
  { k: "Debate intensity", render: (s) => `${s.messages} messages` },
];

function Compare() {
  const [list, setList] = useState<CompareSetup[]>(COMPARE_SETUPS);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchCompareSetups();
      if (data?.length) {
        setList(data);
        toast.success("Loaded Single, Silent, and Debate comparisons from API");
      }
    } catch {
      toast("Loaded fallback comparisons");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Experiments"
        title="Compare Setups: Single vs. Silent vs. Debate"
        desc="Same asset, identical market conditions. See how peer challenge in Debate mode improves risk-adjusted returns."
        actions={
          <Button variant="outline" onClick={loadData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh Comparisons
          </Button>
        }
      />
      {list.length === 0 ? (
        <EmptyState title="No setups" desc="Load sample comparisons to begin." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-soft">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="w-48 p-4 text-left font-semibold uppercase tracking-wider text-xs text-muted-foreground">Mode / Metric</th>
                {list.map((s) => (
                  <th key={s.id} className="p-4 text-left">
                    <p className="font-display text-lg font-semibold">{s.name}</p>
                    <p className="font-mono text-xs font-normal text-muted-foreground">{s.id}</p>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((r) => {
                const best = r.best?.(list);
                return (
                  <tr key={r.k} className="border-b border-border last:border-0 hover:bg-muted/20">
                    <td className="p-4 font-medium text-muted-foreground">{r.k}</td>
                    {list.map((s) => (
                      <td key={s.id} className={`p-4 ${best === s.id ? "font-semibold text-primary" : ""}`}>
                        {r.render(s)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
