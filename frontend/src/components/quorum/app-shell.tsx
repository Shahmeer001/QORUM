import { Link, useNavigate } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { BarChart3, GitCompare, Globe2, Home, Info, MessagesSquare, PlayCircle, Plus, Presentation, Radio, Trophy, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSession } from "@/lib/session-store";
import { StatusChip } from "./badges";

const NAV = [
  { to: "/", label: "Overview", icon: Home },
  { to: "/new-session", label: "New Session", icon: Settings2 },
  { to: "/live", label: "Live Session", icon: Radio },
  { to: "/results", label: "Results", icon: Trophy },
  { to: "/replay", label: "Message Replay", icon: MessagesSquare },
  { to: "/simulation", label: "Simulation", icon: BarChart3 },
  { to: "/compare", label: "Compare", icon: GitCompare },
  { to: "/markets", label: "Markets", icon: Globe2 },
  { to: "/about", label: "About", icon: Info },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const { status, presentation, setPresentation, start, onComplete } = useSession();
  const navigate = useNavigate();

  const runPresentation = () => {
    const next = !presentation;
    setPresentation(next);
    if (next) {
      onComplete.current = () => navigate({ to: "/results" });
      navigate({ to: "/live" });
      start();
    }
  };

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
        <Link to="/" className="px-6 pb-6 pt-7">
          <div className="font-display text-2xl font-bold tracking-[0.12em] text-foreground">QUORUM</div>
          <div className="mt-0.5 text-[11px] font-medium text-muted-foreground">Multi-Agent Decision System</div>
        </Link>
        <nav className="flex-1 space-y-0.5 px-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              activeOptions={{ exact: to === "/" }}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
              activeProps={{ className: "bg-sidebar-accent text-sidebar-accent-foreground" }}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-4 text-[11px] text-muted-foreground">Final Year Project · 2026</div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/85 px-6 backdrop-blur">
          <span className="font-display text-lg font-bold tracking-[0.12em] md:hidden">QUORUM</span>
          <StatusChip status={status} />
          <div className="ml-auto flex items-center gap-2">
            <Button variant={presentation ? "default" : "outline"} size="sm" onClick={runPresentation}>
              <Presentation className="h-4 w-4" />
              {presentation ? "Exit Presentation" : "Presentation Mode"}
            </Button>
            <Button size="sm" asChild>
              <Link to="/new-session">
                <Plus className="h-4 w-4" /> New Session
              </Link>
            </Button>
          </div>
        </header>
        <nav className="flex gap-1 overflow-x-auto border-b border-border px-4 py-2 md:hidden">
          {NAV.map(({ to, label }) => (
            <Link key={to} to={to} activeOptions={{ exact: to === "/" }} className="whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium text-muted-foreground" activeProps={{ className: "bg-secondary text-foreground" }}>
              {label}
            </Link>
          ))}
        </nav>
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}

export { PlayCircle };
