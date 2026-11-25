# Mode Comparison — Validation Window (2024-01-01 to 2024-12-31)

> **Preliminary (FYP1).** Knowledge learned on 2022-01-03 to 2023-12-31 only.
> Test window (2025-01-01 to 2026-11-20) is held out.
> No parameters were tuned to favour any mode.

**Evaluation days:** 252  |  **Degraded days (excluded):** 114

## 1. Mode Comparison

| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) | Exposure(%) | Trades | Turnover | Vetoes | RunID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US | SINGLE | +4.60 | [-8.28, +18.11] | 5.51 | 0.73 | 33.3 | 29.8 | 3 | 6.34x | 170 | — |
| US | SILENT_UW | +14.70 | [-7.02, +40.10] | 4.36 | 1.34 | 64.1 | 69.0 | 39 | 86.65x | 0 | — |
| US | SILENT_W | +4.60 | [-8.28, +18.11] | 5.51 | 0.73 | 33.3 | 29.8 | 3 | 6.34x | 170 | — |
| US | DEBATE | +4.60 | [-8.28, +18.11] | 5.51 | 0.73 | 33.3 | 29.8 | 3 | 6.34x | 170 | — |
| CRYPTO | SINGLE | -5.39 | [-15.01, +0.00] | 5.39 | -1.13 | 0.0 | 0.8 | 2 | 3.85x | 249 | — |
| CRYPTO | SILENT_UW | -2.68 | [-21.34, +18.28] | 6.82 | -0.21 | 0.0 | 3.2 | 1 | 1.97x | 244 | — |
| CRYPTO | SILENT_W | -5.39 | [-15.01, +0.00] | 5.39 | -1.13 | 0.0 | 0.8 | 2 | 3.85x | 249 | — |
| CRYPTO | DEBATE | -5.39 | [-15.01, +0.00] | 5.39 | -1.13 | 0.0 | 0.8 | 2 | 3.85x | 249 | — |

## 2. Benchmarks

| Target | Benchmark | Return(%) | B&H×Exposure(%) | Entry Price | Exit Price |
|---|---|---|---|---|---|
| US | Buy-and-Hold | +24.53 | — | 470.52 | 585.96 |
| CRYPTO | Buy-and-Hold | +108.69 | — | 44810.66 | 93517.26 |
| US | Always-Flat | +0.00 | — | — | — |
| CRYPTO | Always-Flat | +0.00 | — | — | — |
| US | Random (mean±std, 200 seeds) | +0.45±6.13 [-13.77, +17.88] | — | — | — |
| CRYPTO | Random (mean±std, 200 seeds) | +8.72±26.40 [-48.08, +124.38] | — | — | — |

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
- Random-timing baseline: uniform BUY/SELL/HOLD per day, long/flat only, 200 seeds.
- Uniform-random-when-triggered is documented in rule_baselines_validation.md as a simplification.
- All fills use the same rules as BarByBarSimulator (SPY: next-open; BTC: first 1h candle at 21:00 UTC cutoff).
- Risk veto counts include both volatility and drawdown overrides.

## 5. Known Limitations (read before citing)

- **The drawdown breaker does not re-arm.** After a breach the position is closed, but the equity peak is not reset, so flat equity stays more than the limit below it and the breaker fires on every later day. This contradicts protocol.md section 10.
- Because of this, SINGLE, SILENT_W and DEBATE results mostly reflect the period before the first breach. Identical returns do **not** show that the modes decide the same way, or that debate adds nothing.
- Section 3 compares post-risk final actions, so differences in consensus during the locked period are hidden.
