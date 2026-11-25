# Mode Comparison — Validation Window (2024-01-01 to 2024-12-31)

> **Preliminary (FYP1).** Knowledge learned on 2022-01-03 to 2023-12-31 only.
> Test window (2025-01-01 to 2026-11-20) is held out.
> Only the drawdown cool-off length was tuned (mode-neutral criterion).

**Evaluation days:** 252  |  **Degraded days (excluded):** 114

## 1. Mode Comparison

| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) | Exposure(%) | Trades | Turnover | Vetoes | RunID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US | SINGLE | +15.82 | [-9.37, +46.31] | 9.49 | 1.25 | 100.0 | 94.8 | 3 | 6.40x | 12 | — |
| US | SILENT_UW | +14.27 | [-6.47, +37.32] | 5.11 | 1.47 | 62.2 | 70.6 | 37 | 82.66x | 2 | — |
| US | SILENT_W | +14.07 | [-11.10, +44.94] | 9.49 | 1.13 | 50.0 | 94.4 | 4 | 8.44x | 12 | — |
| US | DEBATE | +14.07 | [-11.10, +44.94] | 9.49 | 1.13 | 50.0 | 94.4 | 4 | 8.44x | 12 | — |
| CRYPTO | SINGLE | +30.69 | [-27.01, +137.28] | 17.16 | 1.03 | 46.7 | 29.8 | 15 | 33.43x | 147 | — |
| CRYPTO | SILENT_UW | +30.34 | [-28.20, +142.57] | 21.69 | 0.98 | 33.3 | 29.0 | 15 | 31.84x | 168 | — |
| CRYPTO | SILENT_W | +30.69 | [-27.01, +137.28] | 17.16 | 1.03 | 46.7 | 29.8 | 15 | 33.43x | 147 | — |
| CRYPTO | DEBATE | +30.69 | [-27.01, +137.28] | 17.16 | 1.03 | 46.7 | 29.8 | 15 | 33.43x | 147 | — |

## 2. Benchmarks

| Target | Benchmark | Return(%) | MaxDD(%) | Sharpe | Entry Price | Exit Price |
|---|---|---|---|---|---|---|
| US | Buy-and-Hold | +24.53 | 8.41 | 1.82 | 470.52 | 585.96 |
| US | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |
| CRYPTO | Buy-and-Hold | +108.69 | 27.10 | 1.61 | 44810.66 | 93517.26 |
| CRYPTO | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |
| US | Random uniform (mean±std, 200 seeds) | +0.58±6.14 [-13.77, +18.35] | — | — | — | — |
| CRYPTO | Random uniform (mean±std, 200 seeds) | +8.72±26.40 [-48.08, +124.38] | — | — | — | — |

### Per mode: same exposure

Random = long each day with probability equal to the mode's exposure, 200 seeds.

| Target | Mode | Exposure(%) | Mode return(%) | B&H×Exposure(%) | Matched random mean±std [min, max] |
|---|---|---|---|---|---|
| US | SINGLE | 94.8 | +15.82 | +23.26 | +20.95±3.68 [+10.76, +31.10] |
| US | SILENT_UW | 70.6 | +14.27 | +17.33 | +9.15±6.09 [-4.12, +25.30] |
| US | SILENT_W | 94.4 | +14.07 | +23.17 | +20.64±3.89 [+10.42, +31.10] |
| US | DEBATE | 94.4 | +14.07 | +23.17 | +20.64±3.89 [+10.42, +31.10] |
| CRYPTO | SINGLE | 29.8 | +30.69 | +32.35 | +8.25±27.21 [-43.37, +96.53] |
| CRYPTO | SILENT_UW | 29.0 | +30.34 | +31.49 | +7.37±26.60 [-45.85, +92.96] |
| CRYPTO | SILENT_W | 29.8 | +30.69 | +32.35 | +8.25±27.21 [-43.37, +96.53] |
| CRYPTO | DEBATE | 29.8 | +30.69 | +32.35 | +8.25±27.21 [-43.37, +96.53] |

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

- The cool-off lengths (US 5 days, CRYPTO 20 days) were selected on this same 2024 window, so these results are optimistic. See breaker_and_debate.md.
- The drawdown peak is rebased at each re-arm, so total drawdown can exceed the 5% limit.
- A HOLD decision keeps the open position (protocol.md section 10); only a drawdown breach or cool-off flattens it.
- DEBATE equals SILENT_W on every day: no debate changed a stance. See breaker_and_debate.md.
- One year, two assets; the bootstrap intervals are wide and include zero. No mode is shown to be better.
- Section 3 compares post-risk final actions.
- No parameter other than the cool-off length was selected here.
