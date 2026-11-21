import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { OpenClosed } from "@/components/quorum/badges";
import { PageHeader } from "@/components/quorum/ui";
import { fetchMarkets } from "@/lib/api";
import { MARKETS, MARKET_INFO, type MarketInfo } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/markets")({
  head: () => ({
    meta: [
      { title: "Markets — QUORUM" },
      { name: "description", content: "The five markets QUORUM agents cover: PSX, US, FOREX, GOLD and CRYPTO." },
      { property: "og:title", content: "Markets — QUORUM" },
      { property: "og:description", content: "PSX, US, FOREX, GOLD and CRYPTO — one agent each." },
    ],
  }),
  component: Markets,
});

function Markets() {
  const [marketList, setMarketList] = useState<MarketInfo[]>(
    MARKETS.map((m) => MARKET_INFO[m])
  );

  useEffect(() => {
    let unmounted = false;
    fetchMarkets().then((data) => {
      if (!unmounted && data?.length) setMarketList(data);
    });
    return () => { unmounted = true; };
  }, []);

  return (
    <div>
      <PageHeader
        eyebrow="Scope"
        title="Five markets, five agents"
        desc="Any market can be the CHOSEN target; the others join as RELATED agents to add cross-market context. Inactive/closed markets are greyed out."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {marketList.map((i) => {
          const isActive = i.open;
          return (
            <article
              key={i.id}
              className={cn(
                "animate-rise rounded-xl border p-6 shadow-soft transition-all",
                isActive
                  ? "border-primary/40 bg-card text-foreground"
                  : "border-border/60 bg-muted/40 text-muted-foreground opacity-75"
              )}
            >
              <div className="flex items-start justify-between">
                <span className={cn("font-display text-3xl font-bold tracking-wide", isActive ? "text-primary" : "text-muted-foreground")}>
                  {i.id}
                </span>
                <OpenClosed open={i.open} />
              </div>
              <h2 className="mt-2 text-lg font-semibold text-foreground">{i.name}</h2>
              <p className="text-sm">{i.region}</p>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {i.assets.map((a) => (
                  <span key={a} className="rounded border border-border px-2 py-0.5 font-mono text-xs">
                    {a}
                  </span>
                ))}
              </div>
              <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Agent role</p>
              <p className="text-sm text-foreground">Can act as CHOSEN or RELATED</p>
              <p className="mt-4 border-t border-border pt-4 text-sm leading-relaxed">{i.why}</p>
            </article>
          );
        })}
      </div>
    </div>
  );
}
