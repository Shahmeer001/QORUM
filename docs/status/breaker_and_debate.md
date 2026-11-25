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

**Crypto max drawdown by cool-off (%):**

| Cool-off days | single | silent_unweighted | silent_weighted = debate |
|---|---|---|---|
| 1 | 27.40 | 20.39 | 28.75 |
| 3 | 27.97 | 27.57 | 32.68 |
| 5 (chosen) | 29.96 | 25.76 | 35.13 |
| 10 | 26.20 | 18.80 | 26.42 |
| 20 | 23.68 | 21.69 | 18.68 |

The chosen value gives the largest silent_weighted drawdown in the grid. Every cell is far above the 5% limit, because the peak is rebased at each re-arm. The selection rule ignored drawdown.

**Full grid:**

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

All signals come from the agent's **own** last 100 candles (US: daily; CRYPTO: 1-hour). Volatility = std of the last 14 log returns, in %.

**CHALLENGE** (round 1, A reviews B's opening message) requires all of:
- B's opening position differs from A's, and B's is not HOLD; and
- if B says BUY: A's volatility > 2.0 **or** A's RSI > 70; if B says SELL: A's RSI < 35.

**REPLY** (compulsory, by B): B's stance changes only if **B's own volatility > 2.4**. It then becomes HOLD with confidence 58. Otherwise stance and confidence are kept. The challenge's content is not read.

**FINAL** (round 2): BUY becomes HOLD (confidence 62) only if at least 2 board messages mention "volatility" or "rotation" **and** own volatility > 2.0.

So debate can only turn a stance into HOLD, never BUY into SELL or HOLD into a trade. Disagreement alone, however strong, changes nothing. The BUY challenge text says "volatility is elevated" even when RSI triggered it.

## 4. Diagnosis: why DEBATE equals SILENT_W (2024, 252 days)

| Target | Days with disagreement | Days with a CHALLENGE | CHALLENGEs | REPLYs | Stance changes (reply / final) | Confidence changes | Consensus differs |
|---|---|---|---|---|---|---|---|
| US | 133 | 6 | 6 | 6 | 0 / 0 | 0 | 0 |
| CRYPTO | 133 | 6 | 6 | 6 | 0 / 0 | 0 | 0 |

Challenge direction (both targets): CRYPTO to US 4, US to CRYPTO 2. The two targets match because agent signals do not depend on the target; only vote weights do.

| Agent volatility | Median | Max | Days > 2.0 | Days > 2.4 |
|---|---|---|---|---|
| US (daily bars) | 0.72 | 1.54 | 0 | 0 |
| CRYPTO (1-hour bars) | 0.57 | 2.31 | 1 | 0 |

**Finding.** No agent's volatility ever exceeded 2.4 on a decision day, so a reply could not change a stance, and the final-stance rule had at most one eligible day. The rules never fire on 2024 data. The thresholds look like daily-scale numbers, while the CRYPTO agent measures hourly volatility (an inference from the code; no design note confirms the intent).

**Mechanics test.** `tests/unit/test_debate_changes_action.py` builds US = BUY (volatility about 2.45, under the 2.5 risk veto) against CRYPTO = SELL (volatility above 2.0). Silent-weighted gives BUY, debate gives HOLD, both risk-approved. It passes, so the plumbing works. The data had to be built to meet the thresholds. **Rules not changed.**

## 5. HOLD conflict (awaiting decision, nothing implemented)

The simulator closes the position on any HOLD; protocol.md section 10 says consensus HOLD keeps it.

- **Option A:** keep the code, amend protocol.md.
- **Option B:** follow the protocol. HOLD keeps the position; drawdown breach and cool-off still flatten. A volatility override then also keeps the position.

Option B was measured by patching the simulator in memory (cool-off 5, not re-tuned). Format A -> B:

| Target | Mode | Return % | MaxDD % | Sharpe | Exposure % | Trades |
|---|---|---|---|---|---|---|
| US | single | 15.14 -> 15.36 | 5.61 -> 10.10 | 1.34 -> 1.16 | 87.3 -> 95.2 | 9 -> 3 |
| US | silent_unweighted | 14.70 -> 13.81 | 4.36 -> 4.91 | 1.34 -> 1.26 | 69.0 -> 70.6 | 39 -> 37 |
| US | silent_weighted = debate | 15.14 -> 13.61 | 5.61 -> 10.10 | 1.34 -> 1.04 | 87.3 -> 94.8 | 9 -> 4 |
| CRYPTO | single | 19.20 -> 35.69 | 29.96 -> 27.78 | 0.70 -> 1.04 | 36.1 -> 47.2 | 39 -> 25 |
| CRYPTO | silent_unweighted | 71.51 -> 26.34 | 25.76 -> 26.91 | 1.53 -> 0.81 | 52.0 -> 51.2 | 29 -> 29 |
| CRYPTO | silent_weighted = debate | 10.39 -> 15.97 | 35.13 -> 32.79 | 0.47 -> 0.60 | 34.9 -> 45.2 | 39 -> 27 |

**Recommendation: B.** It matches the written protocol and stops "no conviction" from being traded as "sell". It is not better on results: they are mixed, and US drawdown nearly doubles for two rows. If B is adopted, the cool-off grid must be re-run, since 5 was selected under A.

## 6. Separate observation (not fixed)

For US, the simulator marks a day-i position at day i's close although it fills at day i+1's open. Final return is unaffected; daily equity, MaxDD, Sharpe and possibly the drawdown breaker are. The size of the effect has not been measured.
