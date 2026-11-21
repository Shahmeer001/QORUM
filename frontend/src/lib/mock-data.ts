export type Market = "PSX" | "US" | "FOREX" | "GOLD" | "CRYPTO";
export type Action = "BUY" | "SELL" | "HOLD" | "ABSTAIN";
export type MsgType = "RECOMMEND" | "CHALLENGE" | "REPLY" | "FINAL";
export type Role = "CHOSEN" | "RELATED";

export const MARKETS: Market[] = ["PSX", "US", "FOREX", "GOLD", "CRYPTO"];

export interface MarketInfo {
  id: Market;
  name: string;
  region: string;
  assets: string[];
  open: boolean;
  why: string;
}

export const MARKET_INFO: Record<Market, MarketInfo> = {
  PSX: { id: "PSX", name: "Pakistan Stock Exchange", region: "Emerging equities · Karachi", assets: ["OGDC", "HBL", "LUCK", "ENGRO"], open: false, why: "Local risk appetite and PKR-linked flows signal regional sentiment." },
  US: { id: "US", name: "US Equities", region: "Developed equities · NYSE/NASDAQ", assets: ["AAPL", "SPY", "MSFT", "GLD"], open: false, why: "Global risk-on/off driver; real yields move gold and crypto." },
  FOREX: { id: "FOREX", name: "Foreign Exchange", region: "Currencies · 24/5 OTC", assets: ["EURUSD", "USDPKR", "DXY", "USDJPY"], open: true, why: "Dollar strength directly prices gold and commodities." },
  GOLD: { id: "GOLD", name: "Gold", region: "Commodity · Safe haven", assets: ["XAUUSD", "GLD", "IAU"], open: false, why: "Classic hedge; reacts to inflation, yields and fear." },
  CRYPTO: { id: "CRYPTO", name: "Crypto", region: "Digital assets · 24/7", assets: ["BTC-USD", "ETH-USD", "SOL-USD"], open: true, why: "High-beta risk gauge; competes with gold as 'digital gold'." },
};

export interface Message {
  id: string;
  round: number;
  from: Market;
  to: Market | "BOARD";
  type: MsgType;
  position: Action;
  reason: string;
  evidence: string[];
}

export type LogEntry =
  | { kind: "msg"; msg: Message }
  | { kind: "event"; round: number; text: string };

export const MESSAGES: Message[] = [
  { id: "m1", round: 0, from: "GOLD", to: "BOARD", type: "RECOMMEND", position: "BUY", reason: "XAUUSD broke above 20-day high with rising volume; real yields softening.", evidence: ["XAU 20D-high", "US10Y real −8bp"] },
  { id: "m2", round: 0, from: "PSX", to: "BOARD", type: "RECOMMEND", position: "HOLD", reason: "KSE-100 range-bound; no clear safe-haven rotation from local investors.", evidence: ["KSE100 flat", "PKR stable"] },
  { id: "m3", round: 0, from: "US", to: "BOARD", type: "RECOMMEND", position: "BUY", reason: "GLD inflows for 4 sessions; S&P breadth weakening supports hedging.", evidence: ["GLD +4d inflow", "SPX breadth 41%"] },
  { id: "m4", round: 0, from: "FOREX", to: "BOARD", type: "RECOMMEND", position: "HOLD", reason: "DXY consolidating near support; no confirmed dollar breakdown yet.", evidence: ["DXY 103.2 support"] },
  { id: "m5", round: 0, from: "CRYPTO", to: "BOARD", type: "RECOMMEND", position: "SELL", reason: "BTC rallying hard; capital may rotate away from gold into crypto.", evidence: ["BTC +6.2% 24h", "Funding +0.04%"] },
  { id: "m6", round: 1, from: "CRYPTO", to: "GOLD", type: "CHALLENGE", position: "SELL", reason: "Gold breakout lacks confirmation while risk assets surge. Why buy now?", evidence: ["BTC/XAU ratio ↑"] },
  { id: "m7", round: 1, from: "GOLD", to: "CRYPTO", type: "REPLY", position: "BUY", reason: "Breakout holds, but volatility is elevated — I'll accept a softer stance if risk flags it.", evidence: ["ATR 14D +32%"] },
  { id: "m8", round: 1, from: "FOREX", to: "US", type: "CHALLENGE", position: "HOLD", reason: "ETF inflows are lagging; dollar hasn't confirmed weakness.", evidence: ["DXY flat 3d"] },
  { id: "m9", round: 1, from: "US", to: "FOREX", type: "REPLY", position: "BUY", reason: "Agreed it's early, but breadth deterioration still favours a hedge.", evidence: ["VIX 19.4"] },
  { id: "m10", round: 2, from: "CRYPTO", to: "BOARD", type: "FINAL", position: "HOLD", reason: "Rotation risk is real but not strong enough to short gold. Moving to HOLD.", evidence: ["BTC momentum fading"] },
  { id: "m11", round: 2, from: "GOLD", to: "BOARD", type: "FINAL", position: "HOLD", reason: "Volatility too high for a clean entry. Moving to HOLD until ATR normalises.", evidence: ["ATR 14D +32%"] },
  { id: "m12", round: 2, from: "US", to: "BOARD", type: "FINAL", position: "BUY", reason: "Maintaining BUY — hedge demand remains intact.", evidence: ["GLD inflow"] },
  { id: "m13", round: 2, from: "PSX", to: "BOARD", type: "FINAL", position: "HOLD", reason: "No change; local data neutral.", evidence: [] },
  { id: "m14", round: 2, from: "FOREX", to: "BOARD", type: "FINAL", position: "HOLD", reason: "No change; await DXY breakdown.", evidence: [] },
];

export const SUPERVISOR_EVENTS: { round: number; text: string }[] = [
  { round: 0, text: "Supervisor collected 5 initial recommendations" },
  { round: 1, text: "Supervisor routed debate messages" },
  { round: 1, text: "Compulsory replies received · Logged debate round · Turns = 1" },
  { round: 2, text: "Final positions received · Logged debate round · Turns = 2" },
];

export function buildLog(): LogEntry[] {
  const out: LogEntry[] = [];
  for (const r of [0, 1, 2]) {
    const evs = SUPERVISOR_EVENTS.filter((e) => e.round === r);
    if (evs[0] && r > 0) out.push({ kind: "event", round: r, text: evs[0].text });
    MESSAGES.filter((m) => m.round === r).forEach((msg) => out.push({ kind: "msg", msg }));
    evs.slice(r > 0 ? 1 : 0).forEach((e) => out.push({ kind: "event", round: r, text: e.text }));
  }
  return out;
}

export const isVisible = (m: Message) => !MARKET_INFO[m.from].open;

export interface AgentSummary {
  market: Market;
  role: Role;
  initial: Action;
  final: Action;
  confidence: number;
  reason: string;
  detail: string;
}

export const AGENTS: AgentSummary[] = [
  { market: "GOLD", role: "CHOSEN", initial: "BUY", final: "HOLD", confidence: 64, reason: "Breakout valid, but volatility too high.", detail: "Signals: 20D high break, real yields −8bp, ATR up 32%. Accepted challenge from CRYPTO in Round 1." },
  { market: "PSX", role: "RELATED", initial: "HOLD", final: "HOLD", confidence: 55, reason: "Local market neutral, no rotation.", detail: "KSE-100 flat for 5 sessions; PKR stable vs USD." },
  { market: "US", role: "RELATED", initial: "BUY", final: "BUY", confidence: 71, reason: "ETF inflows and weak breadth favour hedge.", detail: "GLD inflows 4 days running; SPX breadth at 41%; VIX 19.4." },
  { market: "FOREX", role: "RELATED", initial: "HOLD", final: "HOLD", confidence: 58, reason: "Dollar not yet confirming weakness.", detail: "DXY consolidating at 103.2 support; no breakdown." },
  { market: "CRYPTO", role: "RELATED", initial: "SELL", final: "HOLD", confidence: 52, reason: "Rotation risk fading; softened to HOLD.", detail: "BTC +6.2% in 24h but momentum slowing; funding rates elevated." },
];

export const SAMPLE_SESSION = {
  id: "QRM-2026-001",
  target: "GOLD" as Market,
  asset: "XAUUSD",
  horizon: "Swing",
  maxTurns: 3,
  turnsUsed: 2,
  consensus: "BUY" as Action,
  finalAction: "HOLD" as Action,
  riskStatus: "Overridden" as const,
  riskNote: "Overridden from BUY to HOLD — 14D volatility (2.9%) exceeded limit (2.5%).",
  timestamp: "12 Oct 2026 · 14:32 PKT",
};

export const EQUITY = [
  { t: "D1", v: 10000 }, { t: "D2", v: 10060 }, { t: "D3", v: 10010 }, { t: "D4", v: 10120 },
  { t: "D5", v: 10190 }, { t: "D6", v: 10080 }, { t: "D7", v: 10150 }, { t: "D8", v: 10240 },
  { t: "D9", v: 10210 }, { t: "D10", v: 10310 }, { t: "D11", v: 10280 }, { t: "D12", v: 10342 },
];

export const TRADES = [
  { entry: "01 Oct 09:30", exit: "02 Oct 15:00", side: "BUY", market: "GOLD", pnl: 142, note: "Breakout entry" },
  { entry: "03 Oct 10:15", exit: "03 Oct 16:40", side: "SELL", market: "GOLD", pnl: -58, note: "Stopped at 1.2%" },
  { entry: "05 Oct 09:45", exit: "07 Oct 14:20", side: "BUY", market: "GOLD", pnl: 196, note: "Trend follow" },
  { entry: "08 Oct 11:00", exit: "08 Oct 15:30", side: "BUY", market: "GOLD", pnl: -84, note: "Volatility spike" },
  { entry: "09 Oct 09:30", exit: "11 Oct 13:10", side: "BUY", market: "GOLD", pnl: 146, note: "Consensus BUY" },
  { entry: "12 Oct 14:32", exit: "—", side: "HOLD", market: "GOLD", pnl: 0, note: "Risk override → HOLD" },
];

export const RISK_EVENTS = [
  { time: "08 Oct 11:02", text: "Intraday drawdown 0.8% — within limit", level: "ok" },
  { time: "10 Oct 13:40", text: "Correlation spike GOLD/US detected — monitored", level: "warn" },
  { time: "12 Oct 14:32", text: "Volatility threshold exceeded (2.9% > 2.5%) → override to HOLD", level: "override" },
];

export interface CompareSetup {
  name: string;
  id: string;
  markets: Market[];
  action: Action;
  turns: number;
  override: boolean;
  pnl: number;
  drawdown: number;
  messages: number;
}

export const COMPARE_SETUPS: CompareSetup[] = [
  { name: "Setup A", id: "QRM-2026-001", markets: ["GOLD", "PSX", "US", "FOREX", "CRYPTO"], action: "HOLD", turns: 2, override: true, pnl: 3.42, drawdown: 1.1, messages: 14 },
  { name: "Setup B", id: "QRM-2026-002", markets: ["GOLD", "US", "FOREX"], action: "HOLD", turns: 3, override: false, pnl: 2.95, drawdown: 0.7, messages: 11 },
  { name: "Setup C", id: "QRM-2026-003", markets: ["GOLD", "CRYPTO"], action: "BUY", turns: 1, override: false, pnl: 4.1, drawdown: 2.6, messages: 5 },
];
