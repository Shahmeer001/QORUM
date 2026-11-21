# QUORUM - Analysis & Requirements Specification

## 1. Executive Summary & Purpose
QUORUM is an autonomous multi-agent financial decision-support and backtesting system. It models cross-market contagion, inter-asset correlation, and macro sentiment through structured peer debates among domain-specialized agents (e.g., PSX, US Equities, FOREX, Gold, Crypto).

## 2. Use Cases

### UC-1: Initiate New Decision Session
- **Actor:** Human Trader / Portfolio Manager
- **Preconditions:** Backend server running, market data adapters initialized.
- **Main Flow:**
  1. User selects target market (e.g., GOLD) and asset (e.g., XAUUSD).
  2. User selects related markets (e.g., US, FOREX, CRYPTO, PSX).
  3. User specifies execution mode (Single Agent, Silent Consensus, Debate).
  4. User sets risk limits (Stop-loss %, Volatility cap %, Drawdown %).
  5. User submits request (`POST /sessions`).
  6. Backend executes debate, calculates consensus, validates through risk layer, and returns completed session.

### UC-2: Live / Step-by-Step Debate Observation
- **Actor:** Human Trader / Auditor
- **Main Flow:**
  1. User watches round-by-round message exchange between agents.
  2. User inspects message evidence, confidence scores, and supervisor interventions.

### UC-3: Comparative Mode Backtesting
- **Actor:** Quantitative Analyst
- **Main Flow:**
  1. User compares outcomes across Single, Silent, and Debate modes on identical historical days.
  2. System contrasts returns, drawdowns, turnover, and risk vetoes.

## 3. System Sequence Diagram (SSD)
```text
Trader                  Frontend                   Backend API                 Supervisor / Risk
  |                        |                            |                              |
  |--- Select Session ---->|                            |                              |
  |--- Click Run --------->|--- POST /sessions -------->|                              |
  |                        |                            |--- Run Debate Loop --------->|
  |                        |                            |<-- Check Risk Limits --------|
  |                        |<-- Session JSON response --|                              |
  |<-- Display Results ----|                            |                              |
```

## 4. Software Requirements Specification (SRS)
- **FR-1:** Agents must strictly adhere to the no-look-ahead visibility rule (open market signals cannot leak into closed sessions).
- **FR-2:** Debate loop must terminate when consensus is reached or `max_turns` is reached.
- **FR-3:** Risk layer must have absolute veto authority over supervisor recommendations.
- **NFR-1 (Deterministic Replay):** Every session must produce identical output given identical random seeds and inputs.
- **NFR-2 (Latency):** Complete simulated debate of 3 turns across 5 agents must finish in under 1 second.
