# Drawdown breaker fix and debate analysis (validation window 2024 only)

## 1. Why the breaker never re-armed

The equity peak was never reset. After a breach the position is flat, so drawdown stays above 5%. The breaker therefore fired again every day, and each firing reset `cooloff_remaining`, so the counter never counted down.

`test_cooloff_re_arms_after_configured_days` used the same `run_simulation` path (with the cool-off patched to 1 day). It passed because it asserted `>= 1` BUY-side trade, and the forced close of the first long is itself BUY-side. Tightened to `>= 2`, it failed on the old code.

**Fix:** drawdown is not re-evaluated during cool-off, and the peak is rebased to current equity at re-arm. New test: `test_breaker_re_arms_on_experiment_code_path`.

## 2. Cool-off grid (after the HOLD change and the equity-marking fix)

Criterion, written to protocol.md (commit 42d5a5c) before this run: per target, lowest mean max-drawdown across the four modes; ties go to the shorter cool-off. It replaces the mean-Sharpe rule.
The grid had been seen under earlier code before the criterion was written, so the choice is not blind.

| Target | Cool-off | single | unweighted | weighted | debate | Mean MaxDD % |
|---|---|---|---|---|---|---|
| US | 1 | 9.71 | 5.11 | 9.71 | 9.71 | 8.560 |
| US | 3 | 9.71 | 5.11 | 9.71 | 9.71 | 8.560 |
| US | 5 (chosen) | 9.49 | 5.11 | 9.49 | 9.49 | 8.395 |
| US | 10 | 12.59 | 5.11 | 12.59 | 12.59 | 10.720 |
| US | 20 | 11.17 | 5.11 | 11.17 | 11.17 | 9.655 |
| CRYPTO | 1 | 25.81 | 22.69 | 28.31 | 28.31 | 26.280 |
| CRYPTO | 3 | 26.39 | 28.70 | 31.85 | 31.85 | 29.698 |
| CRYPTO | 5 | 27.78 | 26.91 | 32.79 | 32.79 | 30.067 |
| CRYPTO | 10 | 25.86 | 22.04 | 25.86 | 25.86 | 24.905 |
| CRYPTO | 20 (chosen) | 17.16 | 21.69 | 17.16 | 17.16 | 18.293 |

US 5 beats 1 and 3 by only 0.165 points. Every crypto mean is far above the 5% limit, because the peak is rebased at each re-arm.

**Full results:**

| Days | Target | Mode | Return % | MaxDD % | Sharpe | Vetoed days | Trades |
|---|---|---|---|---|---|---|---|
| 1 | US | single | 16.78 | 9.71 | 1.3 | 4 | 3 |
| 1 | US | silent_unweighted | 14.27 | 5.11 | 1.47 | 2 | 37 |
| 1 | US | silent_weighted | 15.02 | 9.71 | 1.18 | 4 | 4 |
| 1 | US | debate | 15.02 | 9.71 | 1.18 | 4 | 4 |
| 1 | CRYPTO | single | 55.71 | 25.81 | 1.32 | 30 | 30 |
| 1 | CRYPTO | silent_unweighted | 25.31 | 22.69 | 0.75 | 34 | 39 |
| 1 | CRYPTO | silent_weighted | 42.17 | 28.31 | 1.1 | 32 | 32 |
| 1 | CRYPTO | debate | 42.17 | 28.31 | 1.1 | 32 | 32 |
| 3 | US | single | 15.97 | 9.71 | 1.25 | 8 | 3 |
| 3 | US | silent_unweighted | 14.27 | 5.11 | 1.47 | 2 | 37 |
| 3 | US | silent_weighted | 14.22 | 9.71 | 1.13 | 8 | 4 |
| 3 | US | debate | 14.22 | 9.71 | 1.13 | 8 | 4 |
| 3 | CRYPTO | single | 54.39 | 26.39 | 1.32 | 56 | 26 |
| 3 | CRYPTO | silent_unweighted | 26.26 | 28.7 | 0.77 | 64 | 35 |
| 3 | CRYPTO | silent_weighted | 31.26 | 31.85 | 0.91 | 60 | 28 |
| 3 | CRYPTO | debate | 31.26 | 31.85 | 0.91 | 60 | 28 |
| 5 | US | single | 15.82 | 9.49 | 1.25 | 12 | 3 |
| 5 | US | silent_unweighted | 14.27 | 5.11 | 1.47 | 2 | 37 |
| 5 | US | silent_weighted | 14.07 | 9.49 | 1.13 | 12 | 4 |
| 5 | US | debate | 14.07 | 9.49 | 1.13 | 12 | 4 |
| 5 | CRYPTO | single | 35.69 | 27.78 | 1.04 | 78 | 25 |
| 5 | CRYPTO | silent_unweighted | 26.34 | 26.91 | 0.81 | 90 | 29 |
| 5 | CRYPTO | silent_weighted | 15.97 | 32.79 | 0.6 | 84 | 27 |
| 5 | CRYPTO | debate | 15.97 | 32.79 | 0.6 | 84 | 27 |
| 10 | US | single | 9.2 | 12.59 | 0.79 | 22 | 3 |
| 10 | US | silent_unweighted | 14.27 | 5.11 | 1.47 | 2 | 37 |
| 10 | US | silent_weighted | 9.2 | 12.59 | 0.79 | 22 | 3 |
| 10 | US | debate | 9.2 | 12.59 | 0.79 | 22 | 3 |
| 10 | CRYPTO | single | -0.23 | 25.86 | 0.14 | 119 | 24 |
| 10 | CRYPTO | silent_unweighted | 5.21 | 22.04 | 0.32 | 119 | 28 |
| 10 | CRYPTO | silent_weighted | -0.23 | 25.86 | 0.14 | 119 | 24 |
| 10 | CRYPTO | debate | -0.23 | 25.86 | 0.14 | 119 | 24 |
| 20 | US | single | 8.52 | 11.17 | 0.76 | 42 | 3 |
| 20 | US | silent_unweighted | 14.27 | 5.11 | 1.47 | 2 | 37 |
| 20 | US | silent_weighted | 8.52 | 11.17 | 0.76 | 42 | 3 |
| 20 | US | debate | 8.52 | 11.17 | 0.76 | 42 | 3 |
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

### Threshold reference (not applied)

Replier volatility = std of the last 14 log returns of the agent's own candles at each decision cutoff, on the 501 decision days of the learning window (2022-2023).

| Agent | 90th percentile | Learning max | Learning days > 2.4 | Current threshold | 2024 max |
|---|---|---|---|---|---|
| US (daily) | 1.82 | 2.35 | 0 | 2.4 | 1.54 |
| CRYPTO (1-hour) | 0.96 | 3.12 | 1 | 2.4 | 2.31 |
| Pooled | 1.63 | 3.12 | 1 | 2.4 | 2.31 |

The two agents are on different scales, so one pooled threshold would treat them unequally. The threshold is unchanged.

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

**Decision: B**, implemented. It is chosen to match protocol.md, **not for returns**. The table above was measured at cool-off 5 and before the equity-marking fix; current numbers are in validation_experiment.md.

## 6. US equity marking bug (fixed)

A US order decided on day i fills at day i+1's open, but day i's equity was marked with the new position at day i's close. A hand-built test (`tests/unit/test_equity_marking.py`) gave 9608.46 on day 0 where 10000 was expected. Equity and exposure now use the book held before that fill. The random baseline in the validation script had the same ordering and is fixed too. This also changed US returns, because return is measured from the first equity point (an earlier note saying final return was unaffected was wrong).

CRYPTO shares the marking code, but its fill (open of the candle starting at the cutoff) happens at the mark time, so marking after the fill is correct.

**Resolved afterwards:**
- `run_baselines.py` and `run_rule_baselines.py` had the same bug (hand-built test `tests/unit/test_baseline_marking.py` failed on both). Both now use `app/simulator/signal_engine.py`, which also closes any open position at the last close. R1-R5 were rerun (rule_baselines_validation.md): drawdown, Sharpe, hit rate and some returns moved.
- Return % is now measured from initial capital, and buy-and-hold pays commission.
- `run_baselines.py` was **not run**: it still defaults to the held-out test window.

## 7. Later changes

Sections 3 and 4 describe the original debate thresholds. The thresholds were later changed (protocol.md section 12); both runs are compared in validation_experiment.md section 3.
