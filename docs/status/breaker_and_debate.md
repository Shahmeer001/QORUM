# Drawdown breaker fix and debate analysis (validation window 2024 only)

## 1. Why the breaker never re-armed

The equity peak was never reset. After a breach the position is flat, so drawdown stays above 5%. The breaker therefore fired again every day, and each firing reset `cooloff_remaining`, so the counter never counted down.

`test_cooloff_re_arms_after_configured_days` used the same `run_simulation` path (with the cool-off patched to 1 day). It passed because it asserted `>= 1` BUY-side trade, and the forced close of the first long is itself BUY-side. Tightened to `>= 2`, it failed on the old code.

**Fix:** drawdown is not re-evaluated during cool-off, and the peak is rebased to current equity at re-arm. New test: `test_breaker_re_arms_on_experiment_code_path`.

## 2. Cool-off grid (re-run after the HOLD change)

Selection rule unchanged: highest mean Sharpe over 4 modes x 2 targets. Under option B it picks **1 day** (previously 5).

| Cool-off days | Mean Sharpe | Mean return % |
|---|---|---|
| 1 (chosen) | 1.119 | 28.07 |
| 3 | 1.055 | 25.00 |
| 5 | 0.944 | 18.79 |
| 10 | 0.524 | 5.58 |
| 20 | 0.929 | 20.06 |

**Crypto max drawdown by cool-off (%):**

| Cool-off days | single | silent_unweighted | silent_weighted = debate |
|---|---|---|---|
| 1 | 25.81 | 22.69 | 28.31 |
| 3 | 26.39 | 28.7 | 31.85 |
| 5 | 27.78 | 26.91 | 32.79 |
| 10 | 25.86 | 22.04 | 25.86 |
| 20 | 17.16 | 21.69 | 17.16 |

The selection rule ignores drawdown. Every crypto cell is far above the 5% limit, because the peak is rebased at each re-arm.

**Full grid:**

| Days | Target | Mode | Return % | MaxDD % | Sharpe | Vetoed days | Trades |
|---|---|---|---|---|---|---|---|
| 1 | US | single | 16.31 | 9.76 | 1.22 | 4 | 3 |
| 1 | US | silent_unweighted | 13.81 | 4.91 | 1.26 | 2 | 37 |
| 1 | US | silent_weighted | 14.56 | 9.76 | 1.1 | 4 | 4 |
| 1 | US | debate | 14.56 | 9.76 | 1.1 | 4 | 4 |
| 1 | CRYPTO | single | 55.71 | 25.81 | 1.32 | 30 | 30 |
| 1 | CRYPTO | silent_unweighted | 25.31 | 22.69 | 0.75 | 34 | 39 |
| 1 | CRYPTO | silent_weighted | 42.17 | 28.31 | 1.1 | 32 | 32 |
| 1 | CRYPTO | debate | 42.17 | 28.31 | 1.1 | 32 | 32 |
| 3 | US | single | 15.51 | 9.76 | 1.17 | 8 | 3 |
| 3 | US | silent_unweighted | 13.81 | 4.91 | 1.26 | 2 | 37 |
| 3 | US | silent_weighted | 13.76 | 9.76 | 1.05 | 8 | 4 |
| 3 | US | debate | 13.76 | 9.76 | 1.05 | 8 | 4 |
| 3 | CRYPTO | single | 54.39 | 26.39 | 1.32 | 56 | 26 |
| 3 | CRYPTO | silent_unweighted | 26.26 | 28.7 | 0.77 | 64 | 35 |
| 3 | CRYPTO | silent_weighted | 31.26 | 31.85 | 0.91 | 60 | 28 |
| 3 | CRYPTO | debate | 31.26 | 31.85 | 0.91 | 60 | 28 |
| 5 | US | single | 15.36 | 10.1 | 1.16 | 12 | 3 |
| 5 | US | silent_unweighted | 13.81 | 4.91 | 1.26 | 2 | 37 |
| 5 | US | silent_weighted | 13.61 | 10.1 | 1.04 | 12 | 4 |
| 5 | US | debate | 13.61 | 10.1 | 1.04 | 12 | 4 |
| 5 | CRYPTO | single | 35.69 | 27.78 | 1.04 | 78 | 25 |
| 5 | CRYPTO | silent_unweighted | 26.34 | 26.91 | 0.81 | 90 | 29 |
| 5 | CRYPTO | silent_weighted | 15.97 | 32.79 | 0.6 | 84 | 27 |
| 5 | CRYPTO | debate | 15.97 | 32.79 | 0.6 | 84 | 27 |
| 10 | US | single | 8.76 | 12.59 | 0.73 | 22 | 3 |
| 10 | US | silent_unweighted | 13.81 | 4.91 | 1.26 | 2 | 37 |
| 10 | US | silent_weighted | 8.76 | 12.59 | 0.73 | 22 | 3 |
| 10 | US | debate | 8.76 | 12.59 | 0.73 | 22 | 3 |
| 10 | CRYPTO | single | -0.23 | 25.86 | 0.14 | 119 | 24 |
| 10 | CRYPTO | silent_unweighted | 5.21 | 22.04 | 0.32 | 119 | 28 |
| 10 | CRYPTO | silent_weighted | -0.23 | 25.86 | 0.14 | 119 | 24 |
| 10 | CRYPTO | debate | -0.23 | 25.86 | 0.14 | 119 | 24 |
| 20 | US | single | 8.08 | 11.17 | 0.7 | 42 | 3 |
| 20 | US | silent_unweighted | 13.81 | 4.91 | 1.26 | 2 | 37 |
| 20 | US | silent_weighted | 8.08 | 11.17 | 0.7 | 42 | 3 |
| 20 | US | debate | 8.08 | 11.17 | 0.7 | 42 | 3 |
| 20 | CRYPTO | single | 30.69 | 17.16 | 1.03 | 147 | 15 |
| 20 | CRYPTO | silent_unweighted | 30.34 | 21.69 | 0.98 | 168 | 15 |
| 20 | CRYPTO | silent_weighted | 30.69 | 17.16 | 1.03 | 147 | 15 |
| 20 | CRYPTO | debate | 30.69 | 17.16 | 1.03 | 147 | 15 |

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

## 5. HOLD conflict (option B adopted)

Before the change the simulator closed the position on any HOLD; protocol.md section 10 says consensus HOLD keeps it.

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

**Decision: B**, implemented, for consistency with the protocol rather than for results. The table above is the comparison at cool-off 5; section 2 has the re-run grid, and validation_experiment.md the current numbers at cool-off 1.

## 6. Separate observation (not fixed)

For US, the simulator marks a day-i position at day i's close although it fills at day i+1's open. Final return is unaffected; daily equity, MaxDD, Sharpe and possibly the drawdown breaker are. The size of the effect has not been measured.
