# Drawdown breaker fix and debate analysis (validation window 2024 only)

## 1. Why the breaker never re-armed

The equity peak was never reset. After a breach the position is flat, so drawdown stays above 5%. The breaker therefore fired again every day, and each firing reset `cooloff_remaining`, so the counter never counted down.

`test_cooloff_re_arms_after_configured_days` used the same `run_simulation` path (with the cool-off patched to 1 day). It passed because it asserted `>= 1` BUY-side trade, and the forced close of the first long is itself BUY-side. Tightened to `>= 2`, it failed on the old code.

**Fix:** drawdown is not re-evaluated during cool-off, and the peak is rebased to current equity at re-arm. New test: `test_breaker_re_arms_on_experiment_code_path`.

## 2. Cool-off grid

Selection rule, fixed before the run: highest mean Sharpe over 4 modes x 2 targets.

| Cool-off days | Mean Sharpe | Mean return % |
|---|---|---|
| 1 | 0.804 | 15.35 |
| 3 | 0.985 | 17.40 |
| 5 (chosen) | 1.066 | 21.45 |
| 10 | 1.011 | 21.64 |
| 20 | 0.996 | 19.96 |

The gaps between 3, 5, 10 and 20 are small; this does not show 5 is reliably best.

| Days | Target | Mode | Return % | MaxDD % | Sharpe | Vetoed days | Trades |
|---|---|---|---|---|---|---|---|
| 1 | US | single | 11.14 | 8.58 | 0.9 | 4 | 10 |
| 1 | US | silent_unweighted | 14.7 | 4.36 | 1.34 | 0 | 39 |
| 1 | US | silent_weighted | 11.14 | 8.58 | 0.9 | 4 | 10 |
| 1 | US | debate | 11.14 | 8.58 | 0.9 | 4 | 10 |
| 1 | CRYPTO | single | 10.28 | 27.4 | 0.45 | 30 | 47 |
| 1 | CRYPTO | silent_unweighted | 47.9 | 20.39 | 1.14 | 32 | 41 |
| 1 | CRYPTO | silent_weighted | 8.23 | 28.75 | 0.4 | 32 | 48 |
| 1 | CRYPTO | debate | 8.23 | 28.75 | 0.4 | 32 | 48 |
| 3 | US | single | 15.1 | 5.75 | 1.34 | 8 | 9 |
| 3 | US | silent_unweighted | 14.7 | 4.36 | 1.34 | 0 | 39 |
| 3 | US | silent_weighted | 15.1 | 5.75 | 1.34 | 8 | 9 |
| 3 | US | debate | 15.1 | 5.75 | 1.34 | 8 | 9 |
| 3 | CRYPTO | single | 17.19 | 27.97 | 0.63 | 56 | 40 |
| 3 | CRYPTO | silent_unweighted | 47.81 | 27.57 | 1.15 | 60 | 36 |
| 3 | CRYPTO | silent_weighted | 7.1 | 32.68 | 0.37 | 60 | 41 |
| 3 | CRYPTO | debate | 7.1 | 32.68 | 0.37 | 60 | 41 |
| 5 | US | single | 15.14 | 5.61 | 1.34 | 12 | 9 |
| 5 | US | silent_unweighted | 14.7 | 4.36 | 1.34 | 0 | 39 |
| 5 | US | silent_weighted | 15.14 | 5.61 | 1.34 | 12 | 9 |
| 5 | US | debate | 15.14 | 5.61 | 1.34 | 12 | 9 |
| 5 | CRYPTO | single | 19.2 | 29.96 | 0.7 | 66 | 39 |
| 5 | CRYPTO | silent_unweighted | 71.51 | 25.76 | 1.53 | 84 | 29 |
| 5 | CRYPTO | silent_weighted | 10.39 | 35.13 | 0.47 | 72 | 39 |
| 5 | CRYPTO | debate | 10.39 | 35.13 | 0.47 | 72 | 39 |
| 10 | US | single | 9.29 | 6.87 | 0.88 | 22 | 9 |
| 10 | US | silent_unweighted | 14.7 | 4.36 | 1.34 | 0 | 39 |
| 10 | US | silent_weighted | 9.29 | 6.87 | 0.88 | 22 | 9 |
| 10 | US | debate | 9.29 | 6.87 | 0.88 | 22 | 9 |
| 10 | CRYPTO | single | 29.08 | 26.2 | 0.99 | 97 | 33 |
| 10 | CRYPTO | silent_unweighted | 44.11 | 18.8 | 1.16 | 108 | 28 |
| 10 | CRYPTO | silent_weighted | 28.7 | 26.42 | 0.98 | 97 | 33 |
| 10 | CRYPTO | debate | 28.7 | 26.42 | 0.98 | 97 | 33 |
| 20 | US | single | 8.47 | 7.06 | 0.84 | 42 | 9 |
| 20 | US | silent_unweighted | 14.7 | 4.36 | 1.34 | 0 | 39 |
| 20 | US | silent_weighted | 8.47 | 7.06 | 0.84 | 42 | 9 |
| 20 | US | debate | 8.47 | 7.06 | 0.84 | 42 | 9 |
| 20 | CRYPTO | single | 22.38 | 23.68 | 0.86 | 147 | 24 |
| 20 | CRYPTO | silent_unweighted | 34.06 | 21.69 | 1.07 | 168 | 15 |
| 20 | CRYPTO | silent_weighted | 31.55 | 18.68 | 1.09 | 147 | 23 |
| 20 | CRYPTO | debate | 31.55 | 18.68 | 1.09 | 147 | 23 |

## 3. Current debate rules (unchanged)

- **Challenge:** only if the opponent position differs from the challenger's and is not HOLD. Against BUY: challenger volatility > 2.0% or RSI > 70. Against SELL: challenger RSI < 35. Both use the challenger's own candles.
- **Reply:** the challenged agent moves to HOLD only if its **own** volatility > 2.4%; otherwise it keeps its stance. The challenge content and evidence are not read.
- **Final stance:** BUY becomes HOLD only if at least 2 board messages mention "volatility" or "rotation" and own volatility > 2.0%.
- So only an agent's own volatility can change its position. The BUY challenge text says "volatility is elevated" even when RSI triggered it (see trace).

## 4. Did debate change anything?

| Target | Days | Challenge days | Stance changes | Consensus differs from SILENT_W | Final action differs | Better | Worse |
|---|---|---|---|---|---|---|---|
| US | 252 | 6 | 0 | 0 | 0 | 0 | 0 |
| CRYPTO | 252 | 6 | 0 | 0 | 0 | 0 | 0 |

No day changed, so there are no better or worse days to score.

## 5. Traced day (US target, 2024-04-04)

```
US 2024-04-04 consensus BUY final BUY risk Risk control approved BUY with volatility at 0.7%.
```
