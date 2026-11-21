# Weekly Supervisor Meetings Log

## Meeting 01 — Project Inception & Scope Definition
- **Date:** 2026-10-15
- **Discussion:**
  - Decided on five key markets: PSX, US Equities, FOREX, Gold, Crypto.
  - Defined the role of autonomous agents: each market is represented by its own agent.
  - Established research pipeline to extract empirical candle patterns from historical BTC data.

## Meeting 02 — Data Collection & Pattern Statistics Review
- **Date:** 2026-10-22
- **Discussion:**
  - Reviewed results of `01_download_data.py` to `04_pattern_stats.py`.
  - Supervisor confirmed the 3x3 pattern methodology: `U` (Up), `S` (Same), `D` (Down) with tolerance `0.00025`.
  - Agreed that pattern statistics should be exported to `agent_pattern_knowledge.json`.

## Meeting 03 — Multi-Agent Debate & Board Architecture
- **Date:** 2026-10-29
- **Discussion:**
  - Finalized the typed debate message protocol: `RECOMMEND`, `CHALLENGE`, `REPLY`, `FINAL`.
  - Discussed visibility rules: only closed-market signals can be shared during debate to prevent look-ahead bias.

## Meeting 04 — Supervisor Consensus & Risk Management
- **Date:** 2026-11-05
- **Discussion:**
  - Designed the weighted voting algorithm for the supervisor.
  - Established risk layer veto power: if volatility or drawdown exceed thresholds, supervisor consensus is overridden to `HOLD`.

## Meeting 05 — Integration, Comparison Mode & Final Presentation
- **Date:** 2026-11-12
- **Discussion:**
  - Tested Single Agent vs Silent Consensus vs Debate modes.
  - Verified that debate mode reduces false breakout trades during high-volatility regimes.
  - Finalized deliverables, system test suites, and documentation.

## Meeting 06 — Operational Timing & Design Locking (This Week)
- **Date:** 2026-11-22
- **Key Decision Locked:**
  - Replaced intraday alternating posting with a single daily decision time just after the US market close (4:00 PM Eastern / `America/New_York`).
  - **Data Cut-off Policy:** Every market adapter strictly enforces that candles closing after the US close decision cutoff time are filtered out.
  - **Round-Level Visibility Policy:** In debate round $r$, an agent can see all messages from earlier rounds ($< r$) and its own messages from round $r$. Messages from other agents in round $r$ remain hidden until round $r$ finishes.
  - **Audit Immutability:** Shared board repositories are strictly append-and-read only; any update or deletion attempt is rejected.
  - **Supervisor Sign-off:** Confirmed Daylight Saving Time (EDT vs EST) dynamic UTC offset handling for US close timing.
