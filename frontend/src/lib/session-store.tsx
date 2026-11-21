import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { toast } from "sonner";
import {
  AGENTS,
  EQUITY,
  MESSAGES,
  RISK_EVENTS,
  SAMPLE_SESSION,
  TRADES,
  type Action,
  type Market,
} from "./mock-data";
import { type SessionResultData, createSession } from "./api";

export type SessionStatus = "Idle" | "Running" | "Debating" | "Completed";

export const STEPS = ["Configure", "Data aligned", "Recommendations", "Debating", "Consensus", "Risk check", "Simulation", "Completed"];

/** Each tick = one visible change in the live demo. */
export const TOTAL_TICKS = 8;

export function tickToStep(tick: number) {
  if (tick <= 0) return 0;
  if (tick === 1) return 1;
  if (tick === 2) return 2;
  if (tick <= 4) return 3;
  return Math.min(tick - 1, 7);
}

export function tickToRound(tick: number) {
  if (tick < 2) return -1;
  return Math.min(tick - 2, 2);
}

export interface SessionConfig {
  target: Market;
  related: Market[];
  asset: string;
  horizon: string;
  maxTurns: number;
  stopLoss: number;
  maxVol: number;
  maxDD: number;
  notes: string;
  mode: "single" | "silent" | "debate";
  day: string;
  scenario: "bull" | "bear" | "neutral";
}

export const DEFAULT_SESSION_DATA: SessionResultData = {
  id: SAMPLE_SESSION.id,
  mode: "debate",
  target: SAMPLE_SESSION.target,
  asset: SAMPLE_SESSION.asset,
  horizon: SAMPLE_SESSION.horizon,
  day: "2026-11-10",
  max_turns: SAMPLE_SESSION.maxTurns,
  turns_used: SAMPLE_SESSION.turnsUsed,
  consensus: SAMPLE_SESSION.consensus,
  final_action: SAMPLE_SESSION.finalAction,
  risk_status: SAMPLE_SESSION.riskStatus,
  risk_note: SAMPLE_SESSION.riskNote,
  pnl: 3.42,
  max_drawdown: 1.1,
  win_rate: 60.0,
  timestamp: SAMPLE_SESSION.timestamp,
  messages: MESSAGES,
  agents: AGENTS,
  trades: TRADES as any,
  equity: EQUITY,
  risk_events: RISK_EVENTS,
};

interface Store {
  tick: number;
  playing: boolean;
  status: SessionStatus;
  presentation: boolean;
  config: SessionConfig;
  sessionData: SessionResultData;
  setConfig: (c: SessionConfig) => void;
  setSessionData: (s: SessionResultData) => void;
  start: (data?: SessionResultData) => void;
  togglePause: () => void;
  setPresentation: (v: boolean) => void;
  onComplete: React.MutableRefObject<(() => void) | null>;
}

const Ctx = createContext<Store | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [tick, setTick] = useState(TOTAL_TICKS);
  const [playing, setPlaying] = useState(false);
  const [presentation, setPresentationState] = useState(false);
  const [sessionData, setSessionData] = useState<SessionResultData>(DEFAULT_SESSION_DATA);
  const [config, setConfig] = useState<SessionConfig>({
    target: "GOLD",
    related: ["PSX", "US", "FOREX", "CRYPTO"],
    asset: "XAUUSD",
    horizon: "Swing",
    maxTurns: 3,
    stopLoss: 1.2,
    maxVol: 2.5,
    maxDD: 5,
    notes: "Gold breakout vs crypto rotation — is the hedge trade justified?",
    mode: "debate",
    day: "2026-11-10",
    scenario: "bull",
  });
  const onComplete = useRef<(() => void) | null>(null);
  const [idle, setIdle] = useState(true);

  useEffect(() => {
    if (!playing) return;
    if (tick >= TOTAL_TICKS) {
      setPlaying(false);
      toast.success("Session completed", {
        description: `Final action: ${sessionData.final_action} (${sessionData.risk_status})`,
      });
      onComplete.current?.();
      return;
    }
    const t = setTimeout(() => setTick((x) => x + 1), presentation ? 1300 : 850);
    return () => clearTimeout(t);
  }, [playing, tick, presentation, sessionData]);

  const start = useCallback((customData?: SessionResultData) => {
    if (customData) {
      setSessionData(customData);
    }
    setIdle(false);
    setTick(0);
    setPlaying(true);
  }, []);

  const togglePause = useCallback(() => {
    if (tick >= TOTAL_TICKS) return;
    setPlaying((p) => !p);
  }, [tick]);

  const setPresentation = useCallback((v: boolean) => {
    setPresentationState(v);
    document.documentElement.classList.toggle("presentation", v);
  }, []);

  const step = tickToStep(tick);
  const status: SessionStatus = idle
    ? "Idle"
    : tick >= TOTAL_TICKS
      ? "Completed"
      : step === 3
        ? "Debating"
        : "Running";

  return (
    <Ctx.Provider
      value={{
        tick,
        playing,
        status,
        presentation,
        config,
        sessionData,
        setConfig,
        setSessionData,
        start,
        togglePause,
        setPresentation,
        onComplete,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useSession() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useSession outside provider");
  return c;
}
