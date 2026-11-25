# Mode Comparison — Validation Window (2024-01-01 to 2024-12-31)

> **Preliminary (FYP1).** Knowledge learned on 2022-01-03 to 2023-12-31 only.
> Test window (2025-01-01 to 2026-11-20) is held out.
> Drawdown cool-off lengths were selected on this window; debate thresholds come from the learning window.

**Evaluation days:** 252  |  **Degraded days (excluded):** 114

## 1. Mode Comparison

| Target | Mode | Return(%) | 95% CI | MaxDD(%) | Sharpe | HitRate(%) | Exposure(%) | Trades | Turnover | Vetoes | RunID |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US | SINGLE | +15.82 | [-9.37, +46.31] | 9.49 | 1.25 | 100.0 | 94.8 | 3 | 6.40x | 12 | — |
| US | SILENT_UW | +14.27 | [-6.47, +37.32] | 5.11 | 1.47 | 62.2 | 70.6 | 37 | 82.66x | 2 | — |
| US | SILENT_W | +14.07 | [-11.10, +44.94] | 9.49 | 1.13 | 50.0 | 94.4 | 4 | 8.44x | 12 | — |
| US | DEBATE | +14.07 | [-11.10, +44.94] | 9.49 | 1.13 | 50.0 | 94.4 | 4 | 8.44x | 12 | — |
| CRYPTO | SINGLE | +30.49 | [-27.08, +136.73] | 17.16 | 1.03 | 46.7 | 29.8 | 15 | 33.43x | 147 | — |
| CRYPTO | SILENT_UW | +30.14 | [-31.24, +144.74] | 21.69 | 0.98 | 33.3 | 29.0 | 15 | 31.84x | 168 | — |
| CRYPTO | SILENT_W | +30.49 | [-27.08, +136.73] | 17.16 | 1.03 | 46.7 | 29.8 | 15 | 33.43x | 147 | — |
| CRYPTO | DEBATE | +30.49 | [-27.08, +136.73] | 17.16 | 1.03 | 46.7 | 29.8 | 15 | 33.43x | 147 | — |

## 2. Benchmarks

| Target | Benchmark | Return(%) | MaxDD(%) | Sharpe | Entry Price | Exit Price |
|---|---|---|---|---|---|---|
| US | Buy-and-Hold | +24.42 | 8.41 | 1.81 | 470.52 | 585.96 |
| US | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |
| CRYPTO | Buy-and-Hold | +108.39 | 27.12 | 1.60 | 44810.66 | 93517.26 |
| CRYPTO | Always-Flat | +0.00 | 0.00 | 0.00 | — | — |
| US | Random uniform (mean±std, 200 seeds) | +0.56±6.14 [-13.77, +18.35] | — | — | — | — |
| CRYPTO | Random uniform (mean±std, 200 seeds) | +8.61±26.37 [-48.16, +124.04] | — | — | — | — |

### Per mode: same exposure

Random = long each day with probability equal to the mode's exposure, 200 seeds.

| Target | Mode | Exposure(%) | Mode return(%) | B&H×Exposure(%) | Matched random mean±std [min, max] |
|---|---|---|---|---|---|
| US | SINGLE | 94.8 | +15.82 | +23.16 | +20.87±3.67 [+10.69, +31.01] |
| US | SILENT_UW | 70.6 | +14.27 | +17.25 | +9.10±6.09 [-4.19, +25.30] |
| US | SILENT_W | 94.4 | +14.07 | +23.06 | +20.56±3.88 [+10.34, +31.01] |
| US | DEBATE | 94.4 | +14.07 | +23.06 | +20.56±3.88 [+10.34, +31.01] |
| CRYPTO | SINGLE | 29.8 | +30.49 | +32.26 | +8.15±27.20 [-43.37, +96.53] |
| CRYPTO | SILENT_UW | 29.0 | +30.14 | +31.40 | +7.28±26.59 [-45.93, +92.96] |
| CRYPTO | SILENT_W | 29.8 | +30.49 | +32.26 | +8.15±27.20 [-43.37, +96.53] |
| CRYPTO | DEBATE | 29.8 | +30.49 | +32.26 | +8.15±27.20 [-43.37, +96.53] |

## 3. Debate vs Silent-Weighted — Change Analysis

'learned' = each agent's learning-window 90th percentile ({"US": 1.82, "CRYPTO": 0.96}); 'original' = 2.0 / 2.4 / 2.0 (ablation). The change was decided after seeing the earlier validation result (protocol.md section 12).

Final changes = days the post-risk final action differs from SILENT_W. Better/Worse score the debate action against the next-day return; a change to HOLD cannot be scored and counts as Neutral.

| Target | Thresholds | Challenge days | Replies | Stance changes (reply / final round) | Final changes vs SILENT_W | Better | Worse | Neutral | Return(%) | MaxDD(%) |
|---|---|---|---|---|---|---|---|---|---|---|
| US | learned | 15 | 15 | 1 / 0 | 0 of 252 | 0 | 0 | 0 | +14.07 | 9.49 |
| US | original | 6 | 6 | 0 / 0 | 0 of 252 | 0 | 0 | 0 | +14.07 | 9.49 |
| CRYPTO | learned | 15 | 15 | 1 / 0 | 1 of 252 | 0 | 0 | 1 | +30.49 | 17.16 |
| CRYPTO | original | 6 | 6 | 0 / 0 | 0 of 252 | 0 | 0 | 0 | +30.49 | 17.16 |

## 4. Notes

- Return(%) is measured from initial capital. MaxDD and Sharpe follow the daily curve.
- Bootstrap CIs resample daily PnL% contributions (2000 iterations, seed=42).
- Random-timing baselines are long/flat and run on the shared engine. Matched random draws each day independently, so it trades more than the modes and pays more friction.
- Buy-and-Hold pays the same slippage and commission as the strategies.
- All fills use the same rules as BarByBarSimulator (SPY: next-open; BTC: first 1h candle at 21:00 UTC cutoff).
- Veto counts are days overridden by volatility, drawdown breach or cool-off.

## 5. Known Limitations (read before citing)

- All 2024 figures are optimistic: cool-off lengths (US 5, CRYPTO 20) were selected on this window, and the debate thresholds were changed after seeing its result.
- The cool-off selection ran with the original debate thresholds and before the Return(%) and Buy-and-Hold cost changes. It was not repeated.
- The drawdown peak is rebased at each re-arm, so total drawdown can exceed the 5% limit.
- HOLD keeps the open position (protocol.md section 10); chosen to match the protocol, not for returns.
- In the uniform and matched random baselines a non-BUY day is flat, not 'keep'.
- CRYPTO agents use hourly candles and US agents daily candles.
- One year, two assets; the bootstrap intervals are wide. No mode is shown to be better.

## 6. Future Work

- Debate can only move a stance to HOLD; it cannot turn BUY into SELL or open a trade.
- A reply ignores the challenge's content and evidence: only the replier's own volatility decides. Replies should weigh what the challenger argues.
