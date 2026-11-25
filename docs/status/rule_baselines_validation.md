# Rule-Set Baselines — Validation Window (2024-01-01 to 2024-12-31)

> Preliminary (FYP1). Validation window only.
> Test window (2025-2026) is held out.

**Note on rule-trigger random baseline**: when a rule fires, direction is chosen
uniformly at random (BUY or SELL, 50/50). The supervisor noted this is technically
wrong because it does not preserve the original directional bias of the rule.
It is kept as a sensitivity check; the matched-random-timing baseline (C) is the
primary null model.

Parameters (all from `settings.py`): RSI period 14, buy<30, sell>70;
MACD (12,26,9); Bollinger (20, 2 std).

| Target | Rule | Trader | Return(%) | MaxDD(%) | Sharpe | Hit%(approx) | Exposure% |
|---|---|---|---|---|---|---|---|
| US | R1 | rule | +0.00 | 0.00 | 0.00 | 0.0 | 0.0 |
| US | R1 | trigger_random_mean | +8.21 | 6.43 | 0.91 | 0.0 | 0.0 |
| US | R1 | timing_random_mean | +5.74 | 7.45 | 0.58 | 0.0 | 0.0 |
| US | R2 | rule | +4.85 | 3.96 | 0.70 | 63.6 | 48.8 |
| US | R2 | trigger_random_mean | +2.42 | 8.03 | 0.26 | 0.0 | 0.0 |
| US | R2 | timing_random_mean | +5.74 | 7.45 | 0.58 | 0.0 | 0.0 |
| US | R3 | rule | +18.73 | 6.07 | 1.88 | 100.0 | 43.7 |
| US | R3 | trigger_random_mean | +9.83 | 6.98 | 0.96 | 0.0 | 0.0 |
| US | R3 | timing_random_mean | +5.74 | 7.45 | 0.58 | 0.0 | 0.0 |
| US | R4 | rule | +0.00 | 0.00 | 0.00 | 0.0 | 0.0 |
| US | R4 | trigger_random_mean | +3.66 | 4.81 | 0.67 | 0.0 | 0.0 |
| US | R4 | timing_random_mean | +5.74 | 7.45 | 0.58 | 0.0 | 0.0 |
| US | R5 | rule | +5.60 | 3.30 | 0.89 | 52.4 | 37.7 |
| US | R5 | trigger_random_mean | +2.42 | 8.03 | 0.26 | 0.0 | 0.0 |
| US | R5 | timing_random_mean | +5.74 | 7.45 | 0.58 | 0.0 | 0.0 |
| CRYPTO | R1 | rule | +8.51 | 21.83 | 0.41 | 62.5 | 42.1 |
| CRYPTO | R1 | trigger_random_mean | +41.46 | 25.91 | 1.00 | 0.0 | 0.0 |
| CRYPTO | R1 | timing_random_mean | +30.27 | 29.87 | 0.78 | 0.0 | 0.0 |
| CRYPTO | R2 | rule | +9.51 | 40.41 | 0.43 | 37.2 | 49.6 |
| CRYPTO | R2 | trigger_random_mean | +24.14 | 31.11 | 0.65 | 0.0 | 0.0 |
| CRYPTO | R2 | timing_random_mean | +30.27 | 29.87 | 0.78 | 0.0 | 0.0 |
| CRYPTO | R3 | rule | +41.34 | 31.59 | 1.00 | 63.6 | 57.5 |
| CRYPTO | R3 | trigger_random_mean | +52.50 | 26.08 | 1.17 | 0.0 | 0.0 |
| CRYPTO | R3 | timing_random_mean | +30.27 | 29.87 | 0.78 | 0.0 | 0.0 |
| CRYPTO | R4 | rule | +56.62 | 21.65 | 1.31 | 0.0 | 50.0 |
| CRYPTO | R4 | trigger_random_mean | +27.46 | 10.50 | 0.64 | 0.0 | 0.0 |
| CRYPTO | R4 | timing_random_mean | +30.27 | 29.87 | 0.78 | 0.0 | 0.0 |
| CRYPTO | R5 | rule | +6.99 | 29.34 | 0.36 | 45.6 | 46.4 |
| CRYPTO | R5 | trigger_random_mean | +24.14 | 31.11 | 0.65 | 0.0 | 0.0 |
| CRYPTO | R5 | timing_random_mean | +30.27 | 29.87 | 0.78 | 0.0 | 0.0 |
