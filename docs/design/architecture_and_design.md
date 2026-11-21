# QUORUM - System Design & Architecture

## 1. Layered Architecture

```text
┌────────────────────────────────────────────────────────┐
│            Presentation Layer (TanStack Start / React) │
└───────────────────────────▲────────────────────────────┘
                            │ REST / JSON (FastAPI)
┌───────────────────────────▼────────────────────────────┐
│                    API & Service Layer                 │
│  (SessionService, ExperimentService, Route Controllers)│
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│        Multi-Agent Debate & Supervisor Core            │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  Market Agents   │◄─┤ Shared Board │─►│Supervisor│  │
│  │ (Rule/LLM Brain) │  └──────────────┘  └────┬─────┘  │
│  └──────────────────┘                         │        │
│                                          ┌────▼─────┐  │
│                                          │Risk Layer│  │
│                                          └────┬─────┘  │
│                                          ┌────▼─────┐  │
│                                          │Simulator │  │
│                                          └──────────┘  │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│         Data Adapters, Signals & Persistence           │
│  (Synthetic, Binance, Yahoo, SQLite, Knowledge Base)   │
└────────────────────────────────────────────────────────┘
```

## 2. Key Components

1. **Board (`backend/app/board/`):**
   - Append-only repository for typed messages (`RECOMMEND`, `CHALLENGE`, `REPLY`, `FINAL`).
   - Implements the strict `visibility.py` filter to ensure no look-ahead.

2. **Agents (`backend/app/agents/`):**
   - `MarketAgent` instance per active market.
   - Decoupled from strategy via `Brain` protocol (`RuleBrain`, `FakeBrain`).
   - Integrates research pattern statistics from `agent_pattern_knowledge.json`.

3. **Supervisor (`backend/app/supervisor/`):**
   - Coordinates turns, detects agreement/disagreement, calculates weighted consensus, and handles turn caps.

4. **Risk Layer (`backend/app/risk/`):**
   - Enforces volatility checks, stop-loss limits, and drawdown ceilings.
   - Has veto power to override `BUY`/`SELL` into `HOLD` or `ABSTAIN`.

5. **Trade Simulator (`backend/app/simulator/`):**
   - Generates deterministic equity curves, trade logs, and performance metrics.
