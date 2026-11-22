# QUORUM Project Progress Report & Roadmap Status
**Date:** November 22, 2026  
**Scope:** FYP-1 Build Phase (Capstone Implementation)  
**Supervisor:** Dr. Omar Usman Khan  
**Team Members:** Shahmeer (22P-9079), Hassan Bilal Cheema (22P-9072), Talha Zia (22P-9228)

---

## 1. Executive Summary

Today, **Work Packages 1, 3, and 4** were completed, verified, and committed into the repository under strict honesty constraints (no hard-coded curves, no synthetic active data, strict temporal separation, and full execution friction accounted for). The full automated test suite passes with **49/49 tests passing** (`pytest backend/tests`).

The live system successfully ran end-to-end multi-agent debates, real bar-by-bar backtesting across **474 evaluation days** with **215 degraded days** strictly tracked, and served live API queries to the TanStack/React frontend.

---

## 2. Completed Work Packages (Done Today)

### WP1 & WP1 Follow-ups: Orchestrator as Active Monitor & Governance Layer
- **Strict Debate Quorum**: Enforced that Debate mode requires *both* active agents (`US` and `CRYPTO`) to have valid data.
- **Degraded Single-Agent Fallback**: Implemented automatic fallback to degraded single-agent execution on US exchange holidays/closures (where SPY has no candle but BTC trades 24/7), explicitly logging the degraded state to the board and risk events.
- **Thread Safety & Timeout Protection**: Wrapped agent execution in bounded thread execution (`concurrent.futures`) with configurable timeouts (`AGENT_TIMEOUT_SECONDS = 5.0s`), handling exceptions and timeouts cleanly with `Action.ABSTAIN` and `DataStatus.TIMEOUT`/`DataStatus.ERROR`.
- **Typed Agent Data Status**: Added `DataStatus` (`VALID`, `NO_DATA`, `ERROR`, `TIMEOUT`) across domain models (`Message`, `AgentSummary`), replacing string matching in the accuracy tracker.
- **Abstain Protection**: Ensured that missing data or timeout `ABSTAIN` decisions do not degrade or distort historical accuracy weights.
- **Configurable Minimum Consensus Margin**: Added `min_margin` parameter forcing consensus to `HOLD` when the score difference between the top two actions does not exceed the threshold.
- **Board Logging**: Orchestrator health events, quorum results, and degradation warnings are written directly to the append-only board repository.

### WP3: Real Data Adapters & Dynamic Registry Architecture
- **Real SPY Daily Adapter (`USMarketAdapter`)**:
  - Ingests `backend/data_cache/spy_daily.csv` (1,227 trading days from `2022-01-03` to `2026-11-20`).
  - Implements strict day-first date parsing (`DD/MM/YYYY`), ignores time-of-day, and enforces NYSE weekend and holiday closures.
- **Real Binance BTC Hourly Adapter (`BinanceBTCAdapter`)**:
  - Ingests `backend/data_cache/btc_1h.csv` (42,791 1h candles from `2022-01-03 00:00` to `2026-11-20 23:00 UTC`).
  - Corrected data documentation noting the March 24, 2023 Binance matching engine outage (11:27 to 13:00 UTC).
  - Enforces close time calculation (`close_time = open_time + 1h`) and filters out any candle closing after the US cutoff (16:00 ET / 21:00 UTC).
- **Minimal Dynamic Registry Loader**:
  - Loads agent configurations dynamically from `backend/app/config/markets.yaml`.
  - Distinguishes active FYP-1 markets (`US`, `CRYPTO`) from inactive FYP-2 markets (`PSX`, `FOREX`, `GOLD`).

### WP4: Real Bar-by-Bar Replay Simulator & Execution Friction
- **Strict Out-of-Sample Window Split**:
  - **Learning Window (`2022-01-03` to `2024-12-31`)**: Pattern knowledge was rebuilt strictly within this window via `backend/scripts/build_learning_window_knowledge.py` generating `us.json` (753 daily bars) and `crypto.json` (26,255 hourly bars).
  - **Test Window (`2025-01-01` to `2026-11-20`)**: Held out completely untouched for out-of-sample evaluation with **zero parameter tuning**.
- **Removal of Mock/Hardcoded Curves**:
  - Completely purged `base_points = [0, 60, ...]` and static `142.0` trades from `backend/app/simulator/trade_engine.py`.
- **Friction & Fill Execution**:
  - Configured per-market costs in `markets.yaml`:
    - **US (SPY)**: `commission: 0.0005` (0.05%), `slippage: 0.0002` (0.02%)
    - **CRYPTO (BTC)**: `commission: 0.0010` (0.10%), `slippage: 0.0005` (0.05%)
  - Fills: SPY fills at next US trading day Open; BTC fills at cutoff 1h candle Open (21:00 UTC). Position held until next decision.
  - Default Long/Flat; shorting evaluated separately behind `allow_short=True`.
- **Day Classification**:
  - **474 Evaluation Days**: Both markets active and candles valid at cutoff.
  - **215 Degraded Days**: US exchange holidays/weekends, excluded from main evaluation metrics and counted separately.
- **WP4 Unit Tests (`backend/tests/unit/test_simulator_wp4.py`)**:
  - Test (a): Hand-built series matched hand-calculated PnL with fees ($985.30 net PnL).
  - Test (b): Rising vs falling series verified opposite-sign results.
  - Test (c): Perturbation test verified post-cutoff candles are strictly ignored.
  - Test (d): Search test verified zero hard-coded PnL/equity arrays remain.

---

## 3. WP4 Out-of-Sample Results Table (2025-01-01 to 2026-11-20)

*Reported separately per target market (never averaged), with slippage and commission deducted from every trade:*

| Target Market | Shorting Mode | Start Equity | End Equity | Net PnL ($) | Return (%) | Max Drawdown (%) | Hit Rate (%) | Exposure (%) | Trade Count | Turnover |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **US (SPY)** | Long/Flat *(Default)* | $10,000.00 | **$11,187.56** | **+$1,187.56** | **+11.88%** | 10.45% | 43.8% | 73.8% | 32 | 71.45x |
| **US (SPY)** | Long/Short *(Sensitivity)* | $10,000.00 | **$12,285.38** | **+$2,285.38** | **+22.85%** | 51.17% | 42.2% | 81.9% | 45 | 102.24x |
| **CRYPTO (BTC)** | Long/Flat *(Default)* | $10,000.00 | **$5,281.29** | **-$4,703.71** | **-47.11%** | 53.08% | 31.2% | 46.8% | 96 | 136.14x |
| **CRYPTO (BTC)** | Long/Short *(Sensitivity)* | $10,000.00 | **$2,371.97** | **-$7,613.03** | **-76.24%** | 96.17% | 30.3% | 79.3% | 178 | 247.05x |

*Degraded Days Excluded from Main Results:* **215 days** (NYSE holidays and weekends where SPY was closed while BTC traded).

---

## 4. Git Commits Created Today

1. `9b170f6`: `feat(wp1): orchestrator monitor, quorum rule, tie-breaking, empty-candle guard, real data provenance`
2. `00eed63`: `feat(wp1-followup): debate quorum strictness, degraded single-agent fallback, agent timeouts/exceptions, board events, missing-data weights, min margin`
3. `dcbceaa`: `feat(wp3): real data adapters for US and CRYPTO with dynamic registry loader and cutoff boundary`
4. `b05ea86`: `feat(wp4): real bar-by-bar replay simulator with fill execution and friction`

---

## 5. What Tasks Are Still Missing / Next Steps

The following work packages remain on the implementation roadmap:

### 1. WP6: Three-Mode Hypothesis Comparison Experiment
- **Objective**: Run the bar-by-bar historical replay across all 3 modes:
  1. Single Agent (Target in isolation)
  2. Silent Multi-Agent (Parallel recommendations combined without debate)
  3. Debating Multi-Agent (Full 3-turn structured debate)
- **Goal**: Empirically evaluate the core capstone thesis: *Does communication between agents add value beyond silent aggregation?*
- **Deliverable**: Comparative metrics table (Return, Drawdown, Sharpe/Sortino, Turnover) across Single vs Silent vs Debate.

### 2. WP5: Consensus Sensitivity & Accuracy Weight Analysis
- **Objective**: Evaluate sensitivity of consensus decisions to:
  - Minimum winning margin threshold (`min_margin` from 0.0 to 0.3).
  - Accuracy update formulas (Brier score updates vs binary hit-rate adjustments).
  - Tie-breaking rules under evenly divided agent stances.

### 3. WP2 (Remaining Frontend UI Polish)
- **Status**: Backend and Frontend are connected and communicating.
- **Missing Items**:
  - Connect the new historical replay simulation endpoints to a dedicated UI view in the frontend.
  - Surface the degraded day counter and holiday fallback badges directly in the UI session timeline.
  - Ensure the frontend Trade Log tab displays the real trade fills, commission, and slippage breakdowns generated by the new simulation engine.

### 4. WP8: Capstone Project Management & Documentation
- **Status**: Basic architecture documents and meeting logs exist in `docs/`.
- **Missing Items**:
  - Update system design documents (Class Diagram, Sequence Diagrams, ERD) to reflect the new dynamic registry and replay simulator.
  - Finalize the FYP-1 mid-evaluation presentation slides highlighting the working 2-agent system with and without the orchestrator.
  - Formalize weekly supervisor meeting logs with Dr. Omar Usman Khan documenting the approved FYP-1 scope (SPY + BTC + Orchestrator) and FYP-2 roadmap (PSX, Forex, Gold).
