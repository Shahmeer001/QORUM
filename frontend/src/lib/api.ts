import {
  AGENTS,
  COMPARE_SETUPS,
  EQUITY,
  MARKET_INFO,
  MARKETS,
  MESSAGES,
  RISK_EVENTS,
  SAMPLE_SESSION,
  TRADES,
  type Action,
  type AgentSummary,
  type CompareSetup,
  type Market,
  type MarketInfo,
  type Message,
  type Role,
} from "./mock-data";

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000";

export interface SessionResultData {
  id: string;
  run_id?: string | null;
  mode: "single" | "silent" | "debate";
  target: Market;
  asset: string;
  horizon: string;
  day: string;
  max_turns: number;
  turns_used: number;
  consensus: Action;
  final_action: Action;
  risk_status: "Approved" | "Overridden" | "Rejected";
  risk_note: string;
  pnl: number;
  max_drawdown: number;
  win_rate: number;
  timestamp: string;
  messages: Message[];
  agents: AgentSummary[];
  trades: Array<{
    entry: string;
    exit: string;
    side: Action;
    market: Market;
    pnl: number;
    note: string;
  }>;
  equity: Array<{ t: string; v: number }>;
  risk_events: Array<{ time: string; text: string; level: string }>;
}

export interface SessionPayload {
  target: string;
  related: string[];
  asset: string;
  horizon: string;
  maxTurns: number;
  stopLoss: number;
  maxVol: number;
  maxDD: number;
  notes: string;
  mode: string;
  day: string;
  scenario: string;
}

export async function fetchMarkets(): Promise<MarketInfo[]> {
  try {
    const res = await fetch(`${API_BASE}/markets`);
    if (!res.ok) throw new Error("Failed to fetch markets");
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("Backend offline, using fallback markets:", err);
    return MARKETS.map((m) => MARKET_INFO[m]);
  }
}

export async function createSession(payload: SessionPayload): Promise<SessionResultData> {
  try {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, returning synthetic session fallback:", err);
    return {
      id: "QRM-2026-FALLBACK",
      mode: (payload.mode as any) || "debate",
      target: (payload.target as Market) || "GOLD",
      asset: payload.asset || "XAUUSD",
      horizon: payload.horizon || "Swing",
      day: payload.day || "2026-11-10",
      max_turns: payload.maxTurns || 3,
      turns_used: 2,
      consensus: "BUY",
      final_action: "HOLD",
      risk_status: "Overridden",
      risk_note: "Overridden from BUY to HOLD — volatility (2.9%) exceeded limit (2.5%).",
      pnl: 3.42,
      max_drawdown: 1.1,
      win_rate: 60.0,
      timestamp: "12 Oct 2026 · 14:32 PKT",
      messages: MESSAGES,
      agents: AGENTS,
      trades: TRADES as any,
      equity: EQUITY,
      risk_events: RISK_EVENTS,
    };
  }
}

export async function fetchLatestSession(): Promise<SessionResultData> {
  try {
    const res = await fetch(`${API_BASE}/sessions/latest`);
    if (!res.ok) throw new Error("Failed to fetch latest session");
    return await res.json();
  } catch (err) {
    return {
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
  }
}

export async function fetchCompareSetups(params?: { target?: string; scenario?: string }): Promise<CompareSetup[]> {
  try {
    const q = new URLSearchParams();
    if (params?.target) q.append("target", params.target);
    if (params?.scenario) q.append("scenario", params.scenario);
    const res = await fetch(`${API_BASE}/compare?${q.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch compare setups");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, returning mock compare setups:", err);
    return COMPARE_SETUPS;
  }
}
