# Mode Comparison — Validation Window (2024-01-01 to 2024-12-31)

> **Preliminary (FYP1).** Knowledge learned on 2022-01-03 to 2023-12-31 only.
> Test window (2025-01-01 to 2026-11-20) is held out.
> Only the drawdown cool-off length was tuned (mode-neutral criterion).

**Evaluation days:** 252  |  **Degraded days (excluded):** 114

## 1. Mode Comparison

| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) | Exposure(%) | Trades | Turnover | Vetoes | RunID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US | SINGLE | +15.14 | [-7.76, +41.55] | 5.61 | 1.34 | 66.7 | 87.3 | 9 | 19.87x | 12 | — |
| US | SILENT_UW | +14.70 | [-7.02, +40.10] | 4.36 | 1.34 | 64.1 | 69.0 | 39 | 86.65x | 0 | — |
| US | SILENT_W | +15.14 | [-7.76, +41.55] | 5.61 | 1.34 | 66.7 | 87.3 | 9 | 19.87x | 12 | — |
| US | DEBATE | +15.14 | [-7.76, +41.55] | 5.61 | 1.34 | 66.7 | 87.3 | 9 | 19.87x | 12 | — |
| CRYPTO | SINGLE | +19.20 | [-35.67, +131.28] | 29.96 | 0.70 | 38.5 | 36.1 | 39 | 84.49x | 66 | — |
| CRYPTO | SILENT_UW | +71.51 | [-19.54, +270.41] | 25.76 | 1.53 | 27.6 | 52.0 | 29 | 70.91x | 84 | — |
| CRYPTO | SILENT_W | +10.39 | [-40.30, +112.63] | 35.13 | 0.47 | 35.9 | 34.9 | 39 | 80.54x | 72 | — |
| CRYPTO | DEBATE | +10.39 | [-40.30, +112.63] | 35.13 | 0.47 | 35.9 | 34.9 | 39 | 80.54x | 72 | — |

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
| US | SINGLE | 87.3 | +15.14 | +21.42 | +16.09±5.33 [+1.16, +28.01] |
| US | SILENT_UW | 69.0 | +14.70 | +16.94 | +8.32±6.24 [-5.91, +23.37] |
| US | SILENT_W | 87.3 | +15.14 | +21.42 | +16.09±5.33 [+1.16, +28.01] |
| US | DEBATE | 87.3 | +15.14 | +21.42 | +16.09±5.33 [+1.16, +28.01] |
| CRYPTO | SINGLE | 36.1 | +19.20 | +39.25 | +11.86±29.84 [-46.38, +150.45] |
| CRYPTO | SILENT_UW | 52.0 | +71.51 | +56.50 | +25.33±34.89 [-31.65, +109.18] |
| CRYPTO | SILENT_W | 34.9 | +10.39 | +37.96 | +10.73±29.31 [-42.01, +150.45] |
| CRYPTO | DEBATE | 34.9 | +10.39 | +37.96 | +10.73±29.31 [-42.01, +150.45] |

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

- The cool-off length (5 days) was selected on this same 2024 window, so these results are optimistic. See breaker_and_debate.md.
- The drawdown peak is rebased at each re-arm, so total drawdown can exceed the 5% limit.
- A HOLD decision closes any open position in the simulator. protocol.md section 10 says consensus HOLD keeps it. Not changed.
- DEBATE equals SILENT_W on every day: no debate changed a stance. SINGLE matches them on US but not on CRYPTO. See breaker_and_debate.md.
- One year, two assets; the bootstrap intervals are wide and include zero. No mode is shown to be better.
- Section 3 compares post-risk final actions.
- No parameter other than the cool-off length was selected here.
