import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2, Play, Save } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MarketBadge, RoleBadge } from "@/components/quorum/badges";
import { PageHeader, Panel } from "@/components/quorum/ui";
import { MARKETS, type Market } from "@/lib/mock-data";
import { createSession } from "@/lib/api";
import { useSession } from "@/lib/session-store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/new-session")({
  head: () => ({
    meta: [
      { title: "New Decision Session — QUORUM" },
      { name: "description", content: "Configure markets, asset, horizon and risk limits for a QUORUM decision session." },
      { property: "og:title", content: "New Decision Session — QUORUM" },
      { property: "og:description", content: "Configure markets, asset, horizon and risk limits." },
    ],
  }),
  component: NewSession,
});

const CHECKS = ["Fetch & align data", "Agent recommendations", "Debate", "Consensus", "Risk check", "Simulation"];

function NewSession() {
  const { config, setConfig, start, onComplete } = useSession();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const set = <K extends keyof typeof config>(k: K, v: (typeof config)[K]) => setConfig({ ...config, [k]: v });

  const toggleRelated = (m: Market) => {
    if (m === config.target) return;
    set("related", config.related.includes(m) ? config.related.filter((x) => x !== m) : [...config.related, m]);
  };

  const setTarget = (m: Market) => setConfig({ ...config, target: m, related: MARKETS.filter((x) => x !== m) });

  const run = async () => {
    setIsSubmitting(true);
    try {
      const result = await createSession({
        target: config.target,
        related: config.related,
        asset: config.asset,
        horizon: config.horizon,
        maxTurns: config.maxTurns,
        stopLoss: config.stopLoss,
        maxVol: config.maxVol,
        maxDD: config.maxDD,
        notes: config.notes,
        mode: config.mode,
        day: config.day,
        scenario: config.scenario,
      });
      onComplete.current = () => navigate({ to: "/results" });
      start(result);
      navigate({ to: "/live" });
    } catch (err) {
      toast.error("Failed to run session", { description: String(err) });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Step 1"
        title="New Decision Session"
        desc="Pick a target market, execution mode, scenario, and asset. Other markets act as related agents in the debate."
      />
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <Panel>
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Execution Mode">
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-secondary p-1">
                {(["single", "silent", "debate"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => set("mode", m)}
                    className={cn(
                      "rounded-md py-1.5 text-xs font-semibold capitalize",
                      config.mode === m ? "bg-card shadow-soft text-primary" : "text-muted-foreground"
                    )}
                  >
                    {m === "single" ? "Single" : m === "silent" ? "Silent" : "Debate"}
                  </button>
                ))}
              </div>
            </Field>

            <Field label="Market Scenario">
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-secondary p-1">
                {(["bull", "bear", "neutral"] as const).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => set("scenario", s)}
                    className={cn(
                      "rounded-md py-1.5 text-xs font-semibold capitalize",
                      config.scenario === s ? "bg-card shadow-soft text-primary" : "text-muted-foreground"
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </Field>

            <Field label="Target market">
              <Select value={config.target} onValueChange={(v) => setTarget(v as Market)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{MARKETS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}</SelectContent>
              </Select>
            </Field>

            <Field label="Asset / symbol">
              <Input value={config.asset} onChange={(e) => set("asset", e.target.value)} placeholder="XAUUSD, BTC-USD, SPY" className="font-mono" />
            </Field>

            <Field label="Trading Day (YYYY-MM-DD)">
              <Input value={config.day} onChange={(e) => set("day", e.target.value)} placeholder="2026-11-10" className="font-mono" />
            </Field>

            <Field label="Horizon">
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-secondary p-1">
                {["Intraday", "Swing", "Position"].map((h) => (
                  <button key={h} type="button" onClick={() => set("horizon", h)}
                    className={cn("rounded-md py-1.5 text-sm font-medium", config.horizon === h ? "bg-card shadow-soft text-primary" : "text-muted-foreground")}>{h}</button>
                ))}
              </div>
            </Field>

            <Field label="Related markets" className="sm:col-span-2">
              <div className="flex flex-wrap gap-2">
                {MARKETS.map((m) => {
                  const chosen = m === config.target;
                  const on = chosen || config.related.includes(m);
                  return (
                    <button key={m} type="button" onClick={() => toggleRelated(m)} disabled={chosen}
                      className={cn("rounded-lg border px-4 py-2 font-mono text-sm font-semibold transition-colors",
                        chosen ? "border-primary bg-primary text-primary-foreground" : on ? "border-primary bg-primary-soft text-primary" : "border-border text-muted-foreground hover:border-primary/40")}>
                      {m}
                    </button>
                  );
                })}
              </div>
            </Field>

            <Field label="Max debate turns">
              <div className="grid grid-cols-3 gap-1 rounded-lg bg-secondary p-1">
                {[1, 2, 3].map((n) => (
                  <button key={n} type="button" onClick={() => set("maxTurns", n)}
                    className={cn("rounded-md py-1.5 font-mono text-sm font-medium", config.maxTurns === n ? "bg-card shadow-soft text-primary" : "text-muted-foreground")}>{n}</button>
                ))}
              </div>
            </Field>
            <Field label="Stop-loss %"><Input type="number" step="0.1" value={config.stopLoss} onChange={(e) => set("stopLoss", +e.target.value)} /></Field>
            <Field label="Max volatility %"><Input type="number" step="0.1" value={config.maxVol} onChange={(e) => set("maxVol", +e.target.value)} /></Field>
            <Field label="Max drawdown %"><Input type="number" step="0.5" value={config.maxDD} onChange={(e) => set("maxDD", +e.target.value)} /></Field>
            <Field label="Notes / thesis" className="sm:col-span-2">
              <Textarea value={config.notes} onChange={(e) => set("notes", e.target.value)} rows={3} />
            </Field>
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel title="Role assignment">
            <ul className="space-y-2">
              {[config.target, ...config.related.filter((m) => m !== config.target)].map((m) => (
                <li key={m} className="flex items-center justify-between">
                  <MarketBadge market={m} />
                  <RoleBadge role={m === config.target ? "CHOSEN" : "RELATED"} />
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="What will happen">
            <ul className="space-y-2.5">
              {CHECKS.map((c, i) => (
                <li key={c} className="flex items-center gap-3 text-sm">
                  <span className="flex h-5 w-5 items-center justify-center rounded border border-border font-mono text-[10px] text-muted-foreground">{i + 1}</span>
                  {c}{c === "Debate" && <span className="text-muted-foreground">(mode: {config.mode})</span>}
                </li>
              ))}
            </ul>
          </Panel>
          <div className="flex flex-col gap-2">
            <Button size="lg" onClick={run} disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Run Decision Session
            </Button>
            <Button size="lg" variant="outline" onClick={() => toast("Setup saved", { description: `${config.asset} · ${config.target} · ${config.horizon}` })}>
              <Save className="h-4 w-4" /> Save Setup
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</Label>
      {children}
    </div>
  );
}
