# Mode Comparison — Validation Window (2024-01-01 to 2024-12-31)

> **Preliminary (FYP1).** Knowledge learned on 2022-01-03 to 2023-12-31 only.
> Test window (2025-01-01 to 2026-11-20) is held out.
> Only the drawdown cool-off length was tuned (mode-neutral criterion).

**Evaluation days:** 252  |  **Degraded days (excluded):** 114

## 1. Mode Comparison

| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) | Exposure(%) | Trades | Turnover | Vetoes | RunID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US | SINGLE | +16.31 | [-11.00, +47.58] | 9.76 | 1.22 | 100.0 | 97.2 | 3 | 6.42x | 4 | — |
| US | SILENT_UW | +13.81 | [-8.41, +38.32] | 4.91 | 1.26 | 62.2 | 70.6 | 37 | 82.66x | 2 | — |
| US | SILENT_W | +14.56 | [-12.19, +45.28] | 9.76 | 1.10 | 50.0 | 96.8 | 4 | 8.47x | 4 | — |
| US | DEBATE | +14.56 | [-12.19, +45.28] | 9.76 | 1.10 | 50.0 | 96.8 | 4 | 8.47x | 4 | — |
| CRYPTO | SINGLE | +55.71 | [-28.15, +247.34] | 25.81 | 1.32 | 40.0 | 54.4 | 30 | 75.58x | 30 | — |
| CRYPTO | SILENT_UW | +25.31 | [-43.24, +181.79] | 22.69 | 0.75 | 25.6 | 64.3 | 39 | 89.67x | 34 | — |
| CRYPTO | SILENT_W | +42.17 | [-33.94, +214.61] | 28.31 | 1.10 | 37.5 | 54.0 | 32 | 75.43x | 32 | — |
| CRYPTO | DEBATE | +42.17 | [-33.94, +214.61] | 28.31 | 1.10 | 37.5 | 54.0 | 32 | 75.43x | 32 | — |

## 2. Benchmarks

| Target | Benchmark | Return(%) | MaxDD(%) | Sharpe | Entry Price | Exit Price |
|---|---|---|---|---|---|---|
| US | Buy-and-Hold | +24.53 | 8.41 | 1.82 | 470.52 | 585.96 |
| US | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |
| CRYPTO | Buy-and-Hold | +108.69 | 27.10 | 1.61 | 44810.66 | 93517.26 |
| CRYPTO | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |
| US | Random uniform (mean±std, 200 seeds) | +0.45±6.13 [-13.77, +17.88] | — | — | — | — |
| CRYPTO | Random uniform (mean±std, 200 seeds) | +8.72±26.40 [-48.08, +124.38] | — | — | — | — |

### Per mode: same exposure

Random = long each day with probability equal to the mode's exposure, 200 seeds.

| Target | Mode | Exposure(%) | Mode return(%) | B&H×Exposure(%) | Matched random mean±std [min, max] |
|---|---|---|---|---|---|
| US | SINGLE | 97.2 | +16.31 | +23.85 | +21.91±2.73 [+15.72, +31.98] |
| US | SILENT_UW | 70.6 | +13.81 | +17.33 | +8.84±6.07 [-4.12, +24.80] |
| US | SILENT_W | 96.8 | +14.56 | +23.75 | +21.70±2.87 [+13.94, +31.98] |
| US | DEBATE | 96.8 | +14.56 | +23.75 | +21.70±2.87 [+13.94, +31.98] |
| CRYPTO | SINGLE | 54.4 | +55.71 | +59.09 | +27.84±34.57 [-34.77, +145.99] |
| CRYPTO | SILENT_UW | 64.3 | +25.31 | +69.87 | +41.64±41.23 [-33.07, +197.89] |
| CRYPTO | SILENT_W | 54.0 | +42.17 | +58.66 | +26.91±34.59 [-38.57, +145.99] |
| CRYPTO | DEBATE | 54.0 | +42.17 | +58.66 | +26.91±34.59 [-38.57, +145.99] |

## 3. Debate vs Silent-Weighted — Change Analysis

Days where DEBATE final_action ≠ SILENT_WEIGHTED final_action.
'Better/Worse' scored against the sign of the realised next-day return.
HOLD actions are excluded from scoring (no directional conviction).

| Target | Total days | Days changed | % changed | Better | Worse | Neutral |
|---|---|---|---|---|---|---|
| US | 252 | 0 | 0.0% | 0 | 0 | 0 |
| CRYPTO | 252 | 0 | 0.0% | 0 | 0 | 0 |

## 4. Notes

- Bootstrap CIs resample daily PnL% contributions (2000 iterations, seed=42).
- Random-timing baselines are long/flat. Matched random draws each day independently, so it trades more than the modes and pays more friction.
- Buy-and-Hold return and curve include slippage but no commission; strategies pay both.
- Uniform-random-when-triggered is documented in rule_baselines_validation.md as a simplification.
- All fills use the same rules as BarByBarSimulator (SPY: next-open; BTC: first 1h candle at 21:00 UTC cutoff).
- Veto counts are days overridden by volatility, drawdown breach or cool-off.

## 5. Known Limitations (read before citing)

- The cool-off length (1 day) was selected on this same 2024 window, so these results are optimistic. See breaker_and_debate.md.
- The drawdown peak is rebased at each re-arm, so total drawdown can exceed the 5% limit.
- A HOLD decision keeps the open position (protocol.md section 10); only a drawdown breach or cool-off flattens it.
- DEBATE equals SILENT_W on every day: no debate changed a stance. See breaker_and_debate.md.
- One year, two assets; the bootstrap intervals are wide and include zero. No mode is shown to be better.
- Section 3 compares post-risk final actions.
- No parameter other than the cool-off length was selected here.
