# Rule-Set Baselines — Validation Window (2024-01-01 to 2024-12-31)

> Preliminary (FYP1). Validation window only; the test window is held out.

- `rule`: follows the signal. BUY = long, SELL = flat, no signal = keep.
- `trigger_random_mean`: when the rule fires, BUY or SELL 50/50 (200 seeds). A sensitivity check only: it does not keep the rule's directional bias.
- `timing_random_mean`: long each day with probability equal to that rule's exposure, otherwise flat (200 seeds). The primary null model. It trades more often than the rule, so it pays more friction.
- All run on `app/simulator/signal_engine.py`; open positions are closed at the last close. Return(%) is from initial capital. Hit% and Exposure are not reported for random rows.
- Parameters (`settings.py`): RSI 14, buy<30, sell>70; MACD (12,26,9); Bollinger (20, 2 std).

| Target | Rule | Trader | Return(%) | MaxDD(%) | Sharpe | Hit% | Exposure% |
|---|---|---|---|---|---|---|---|
| US | R1 | rule | +0.00 | 0.00 | 0.00 | 0.0 | 0.0 |
| US | R1 | trigger_random_mean | +8.17 | 6.25 | 0.92 | — | — |
| US | R1 | timing_random_mean | +0.00 | 0.00 | 0.00 | — | — |
| US | R2 | rule | +4.85 | 3.75 | 0.73 | 63.6 | 48.8 |
| US | R2 | trigger_random_mean | +2.58 | 7.83 | 0.33 | — | — |
| US | R2 | timing_random_mean | +1.70 | 8.06 | 0.23 | — | — |
| US | R3 | rule | +18.65 | 6.07 | 1.91 | 75.0 | 43.3 |
| US | R3 | trigger_random_mean | +9.78 | 6.97 | 1.01 | — | — |
| US | R3 | timing_random_mean | +0.68 | 8.03 | 0.12 | — | — |
| US | R4 | rule | +0.00 | 0.00 | 0.00 | 0.0 | 0.0 |
| US | R4 | trigger_random_mean | +3.62 | 4.79 | 0.71 | — | — |
| US | R4 | timing_random_mean | +0.00 | 0.00 | 0.00 | — | — |
| US | R5 | rule | +5.60 | 3.09 | 0.98 | 52.4 | 37.7 |
| US | R5 | trigger_random_mean | +2.58 | 7.83 | 0.33 | — | — |
| US | R5 | timing_random_mean | -0.14 | 7.90 | 0.02 | — | — |
| CRYPTO | R1 | rule | +8.35 | 21.83 | 0.40 | 55.6 | 42.1 |
| CRYPTO | R1 | trigger_random_mean | +41.36 | 25.91 | 1.00 | — | — |
| CRYPTO | R1 | timing_random_mean | +16.40 | 30.03 | 0.48 | — | — |
| CRYPTO | R2 | rule | +9.51 | 40.41 | 0.43 | 37.2 | 49.6 |
| CRYPTO | R2 | trigger_random_mean | +23.95 | 31.11 | 0.65 | — | — |
| CRYPTO | R2 | timing_random_mean | +22.53 | 31.44 | 0.59 | — | — |
| CRYPTO | R3 | rule | +41.13 | 31.59 | 1.00 | 58.3 | 57.5 |
| CRYPTO | R3 | trigger_random_mean | +52.40 | 26.08 | 1.17 | — | — |
| CRYPTO | R3 | timing_random_mean | +30.27 | 32.21 | 0.73 | — | — |
| CRYPTO | R4 | rule | +56.39 | 21.65 | 1.31 | 100.0 | 50.0 |
| CRYPTO | R4 | trigger_random_mean | +27.35 | 10.50 | 0.64 | — | — |
| CRYPTO | R4 | timing_random_mean | +22.50 | 31.53 | 0.59 | — | — |
| CRYPTO | R5 | rule | +6.99 | 29.34 | 0.36 | 45.6 | 46.4 |
| CRYPTO | R5 | trigger_random_mean | +23.95 | 31.11 | 0.65 | — | — |
| CRYPTO | R5 | timing_random_mean | +19.13 | 30.88 | 0.54 | — | — |

End of report: 30 rows (2 targets x 5 rules x 3 traders).
