# QUORUM Evaluation Protocol
**Project:** QUORUM — Governed Multi-Agent Decision Engine (FYP1)
**Status:** Preliminary (FYP1) — rules frozen at tag `rules-freeze-v2`

---

## 1. Void Earlier Test-Window Run

An earlier run on the test window (2025-01-01 to 2026-11-20) was produced before the
correctness fixes in commit `e6eadb4` (Sharpe sign, short-selling cash accounting, B&H
exposure-scaled benchmark). The rules were otherwise unchanged at that point, but the
metrics were wrong. Those numbers are **void** and must not be cited. They are marked
STALE in `TODAY_PROGRESS_AND_REMAINING_TASKS.md` §3.

---

## 2. Window Definitions

| Window | Date range | Purpose |
|---|---|---|
| Learning (validation runs) | 2022-01-03 – 2023-12-31 | Pattern knowledge in `knowledge_val/`; debate thresholds |
| Learning (test run) | 2022-01-03 – 2024-12-31 | Pattern knowledge in `knowledge/`; test-run debate thresholds |
| Validation | 2024-01-01 – 2024-12-31 | Parameter selection, rule tuning, mode comparison |
| Test (held-out) | 2025-01-01 – 2026-11-20 | Looked at **exactly once**, from the frozen tag |

Validation used knowledge learned from **2022 to 2023** only, so learning and validation do not
overlap there. The test run relearns from **2022 to 2024**: by then 2024 is past data relative
to the test window.

> **Rule**: All development (rule thresholds, min_margin, risk limits, signal weights) must be
> chosen on the validation split only. The test window is opened once, at the end, and the
> numbers reported are final.

---

## 3. Rules-Freeze Protocol

The freeze is the git tag `rules-freeze-v2`, on the commit that contains this table. It replaces
`rules-freeze-v1`; see section 14.
Hashes are SHA-256 with CRLF normalised to LF. `run_final_test.py` recomputes them and refuses
to run on any difference. The data CSVs are not in git; their hashes are listed here.

| File | SHA-256 |
|---|---|
| `backend/app/__init__.py` | `f1fd8cdc34bbdeb277561979b2a792a2fc19047b2eb53946d4e6d181a49d84f4` |
| `backend/app/adapters/__init__.py` | `783d83edced9fd8c994c85537773028bc8777439c254ee3f356f688e345a776f` |
| `backend/app/adapters/base.py` | `9d8fcea99326b6c062ac82c8fde00350c8be2ad0d28c85231c779cd84216b508` |
| `backend/app/adapters/binance_btc.py` | `5deb2450f593520ee1d71a356f107a21e94529616fef6d0ffdd3daed339c8e0b` |
| `backend/app/adapters/synthetic.py` | `023f9c55b0a40beb957b32b1d72c9d790676f06aa5ce08e64f86516e773f9ea8` |
| `backend/app/adapters/us_spy.py` | `1106c7c3a424c2fed36c7b9c7b5259f4ee52f3f71aee6f742e40d3e1d6637503` |
| `backend/app/agents/__init__.py` | `4b78d339d6a08a09591f42ee6c26a85e1dc8106035a85d6d915912435706d1ca` |
| `backend/app/agents/brains/__init__.py` | `c4dfbbafac0f8bec7243c4efb6cc1e613249940b361fff1527cc60101daa82ec` |
| `backend/app/agents/brains/base.py` | `1cdf4b5ac35aedc3ba2b9a99dc2c3f65e0da5751de1d6ddbf11483ba68f1fa2e` |
| `backend/app/agents/brains/fake_brain.py` | `132d1c4cb689064b7f34b9f3f1b4627f8fce07f79cb338199cd3eff615443a45` |
| `backend/app/agents/brains/rule_brain.py` | `825c7dd4ac921f4ce44dab8f4ad8a9426c2666292c19b56c53e059c7c6d4f320` |
| `backend/app/agents/market_agent.py` | `b78ed8cfe57f369bb27dbedb5998c37d536ea2e0d144a4ab91e357ceb5e31323` |
| `backend/app/agents/state.py` | `8f0c995e893185427594536a5c356ed85e12e6db65e576447b8f7360edb1c077` |
| `backend/app/api/__init__.py` | `b166fb342b252b0d438d0c07b5d5cde0ba88212c77165816e523320379b82440` |
| `backend/app/api/deps.py` | `1c6f549e481cffe608136c652d6bb5ec4fb8a4cc36810ed13f2e833d44ab3c75` |
| `backend/app/api/routes_compare.py` | `fc9c5d17688ba2f8fe9687aad9776037776e377e7ff5e917b8b42b5024fb09cd` |
| `backend/app/api/routes_markets.py` | `858ff14228e278627329b492b502a59bf5c98d0254ad6dd8711a820005578f6b` |
| `backend/app/api/routes_sessions.py` | `dddc8e1bcb6653a77becc904d710253e88bdbfa6184bba5b21994845153466a3` |
| `backend/app/api/schemas.py` | `68bccb166111e963fff0a4f06dbfa2635b9f6336d8965db23a6a636973a5085d` |
| `backend/app/board/__init__.py` | `18faf6448ef9f2a66bde77a64364cb66884c10d4653a07acdc4e5c0bc9d7f9a5` |
| `backend/app/board/memory_repo.py` | `24df7efd9313096cb5543b64cf96cea15f9ac79c5bbe85f0cd821ff256e9c512` |
| `backend/app/board/repository.py` | `94cc798f6477e6456429baa60bafa0038425bdacfb103de00bb6517fabda847c` |
| `backend/app/board/sql_repo.py` | `baf88ec36dc1663e28c688916c077cb3b6c58e7f4c830dfe3dfe69f8c4bc9253` |
| `backend/app/board/visibility.py` | `0bfe03cdf6791dc911e8602ef32b518c24eb9df59dcc86ce98f13ccdc6b62706` |
| `backend/app/config/__init__.py` | `96359b5962f995e476004358894046711b3cd40ea6a2c5d9865e54a288cf479e` |
| `backend/app/config/debate_thresholds.json` | `7e0923d534532ec2f61664931d707eaa9d2f2364bcaaa665ec33e414ab394682` |
| `backend/app/config/debate_thresholds_test.json` | `306ae400b21b11d75180a8c31c11567ce1f44ce3bdc3995f95c63c37538f5245` |
| `backend/app/config/markets.yaml` | `f8507820c61f9cf5ae4854e502dc0dee4ad21bdc0ca81c333ebef8ff471b0158` |
| `backend/app/config/settings.py` | `4db27d4fa4f5f2f010c950c42269d5dc9da060b23ffb83f4d2c546085680794a` |
| `backend/app/db/connection.py` | `51f6461abc0bf62f95cf93597baaeaac3d5a185bad45db4856dd9899070da605` |
| `backend/app/db/tables.py` | `f1daa60affc5eaea30660044c049f0640ee55096d243681e31275de31bc84ba4` |
| `backend/app/domain/__init__.py` | `cc1d5502912f9a1d8247412e5972a2ceef967455a3a4bea9a8b8273458abc6f6` |
| `backend/app/domain/enums.py` | `1d0cb269172c321a362f54495f5ad068253238b53f6e7d7294ea8128eb6c55c7` |
| `backend/app/domain/models.py` | `547c1cbd868c46b0a407721a7114324a59c7d0c43d8fd9a57a832045a3b96902` |
| `backend/app/main.py` | `ff8576de12aef7eabaee64d0e5a608a180c82a2ea2370a3e17ad7ea190257f14` |
| `backend/app/modes/__init__.py` | `5612abcdfc12c1a638b1a00b83b52588e824bfc26ffb0e236430b8e57473ba09` |
| `backend/app/modes/debate.py` | `ad5f1133c3b1144f3df21e6f7609ae273ddd33b24949f20494443ac3ac6054c2` |
| `backend/app/modes/dispatch.py` | `66a2e12f242820fe5f13a8839bfa5a313146ec7b9fe9dcf074052ad4e1519039` |
| `backend/app/modes/runner.py` | `c03743f527de3135f16a91a394a73a6d1f6d79cef010b2efb8bc602e8b1846de` |
| `backend/app/modes/silent.py` | `55966368a065544ee61026627286c214288d1105b148204b2d2ee1288ea77bbe` |
| `backend/app/modes/single.py` | `af8de1283441ddbb98947a0301b2b535b9d2c8ee4d2744e5bd8077e2084eea54` |
| `backend/app/orchestrator/__init__.py` | `f380453af11c0f1e12a6e4c7b5eafaa50c0bb97313b4f1712ed1c9ef2882759c` |
| `backend/app/orchestrator/session_orchestrator.py` | `57e6560636797579242a95888dfc0b7c979f9a49a19fbd68f813bd29385c7e46` |
| `backend/app/risk/__init__.py` | `e5211960e12af5c796b0a8ff6efc15e1d7e05de2700929f5f24da60c3f7b151f` |
| `backend/app/risk/risk_layer.py` | `1da93b7fe60a06f50b750dfd91f8f8dcd021125edb6a309d514b38f8894add90` |
| `backend/app/risk/rules.py` | `512388cb67db5ced725c5fccb0199e43fec88106dd8544e69c7a31e254e2e938` |
| `backend/app/services/__init__.py` | `d6dda6ba727fd82772227a1440a0d2c79871e8295f8b6510ff3e8b88d147dbae` |
| `backend/app/services/experiment_service.py` | `5f5f3ff38068cb7835a9dac63c3b54bb8020e47590b2508ce9ca2c8c1f019bf1` |
| `backend/app/services/run_persistence.py` | `c86900259e141a1f94437c0258121cfec26a45020bbec82d9225a004ea3da44c` |
| `backend/app/services/session_service.py` | `c3f40876bee5f0af72fafed2b11049028409dbd9fd968c079b2f75355ba3c195` |
| `backend/app/signals/__init__.py` | `9d178c9cfccdd6e3acf177b88336facd95a78334a6d0b76e216e8794ebd8764a` |
| `backend/app/signals/bollinger.py` | `a755ea32026b2179cd639a434e25395c95dc9f81756ee00d0f1bc461810d57b1` |
| `backend/app/signals/candle_patterns.py` | `8bf59db22925d092a0ce5e88f92a44f89813aa428a3ded35abb11d99cd9e4a75` |
| `backend/app/signals/knowledge_loader.py` | `b2838c0c59113d0cdb77f7d374b0d5710c007324bc37127958de0c12d2ae347a` |
| `backend/app/signals/macd.py` | `1a392c099ce624013bbde2aa675be86a985be3c55251ac105edb23c0d639288a` |
| `backend/app/signals/rsi.py` | `37549875ca25b904eaf62a02ec1d247bc3b8ffd2f474d07105e4f8f5ec4f313d` |
| `backend/app/signals/rule_sets.py` | `bae80d097d86216e5eca720994cfc53f9a1e533710d3d57b54c9340c038e18e4` |
| `backend/app/signals/volatility.py` | `e2bea99d302d74382108a4c43ed048b70978f86e480eb4ffb38898453bfe494c` |
| `backend/app/simulator/__init__.py` | `ef6eb74aefab7ba95d0760e0f3083858a021a38a69dedcd63f80d88da1b4acdf` |
| `backend/app/simulator/metrics.py` | `55f0ce13d3e6b299cd7eb819bfbd23a35f65ffb752f085cdde86950b9b4b201d` |
| `backend/app/simulator/replay.py` | `9566fcaf22e72e7f681773961e984c1c16e4ee1a12ca777013fa65bce5f67c94` |
| `backend/app/simulator/replay_simulator.py` | `bceecc0738abbbc7f967b43b4ecb112d8d5629cf5b1ac30be0ae8ede2759d7c0` |
| `backend/app/simulator/signal_engine.py` | `8d5c6f39b51e1df75bf55d520d49801e3df6c62148c966bf99ec1947e3fcc32a` |
| `backend/app/simulator/trade_engine.py` | `0d1e0532a58ddf2d860beb01b351e20b02929fef03f52462bc46700932bb1708` |
| `backend/app/supervisor/__init__.py` | `5c3d1fbc251e666453e29beafbc49cef8b8e89a27b64c94c1026fc313561cb5d` |
| `backend/app/supervisor/accuracy.py` | `d78af904f3c49d1d6f9a371a3df30422f36381c6597a280d8b42113ef0e56cb4` |
| `backend/app/supervisor/accuracy_bookkeeper.py` | `8a084a52ddf0b597f09a2b5c54a07246f68793db4f9b888a97952b67c13b1136` |
| `backend/app/supervisor/consensus.py` | `067e9b4928a4ef67c9be6500cbb81221210fc0d49d0ae8da46e22dcb4759d134` |
| `backend/app/supervisor/debate_loop.py` | `d45bf456f0c8ba43b60c0d640527dc67b803ce5373fafb5dcaae8ccced6983f4` |
| `backend/app/supervisor/events.py` | `1334574ef22ef260539289de48dc7e38aac143fd5a36b75e335da2c816415864` |
| `backend/app/supervisor/live_accuracy.py` | `849257269ea22955ebd5a2858edbd090ebdb44514c870408bad54d612c5aedd5` |
| `backend/data_cache/btc_1h.csv` | `3dddb0563c3362f3ee1e21e7ded9542f8b1b4ae344bb20bb89c0e8c59c2c7feb` |
| `backend/data_cache/spy_daily.csv` | `cf84eb64b842aa10198809ec147cfe3fef49c7fd9a19429a7a257daa6dd828e5` |
| `backend/knowledge/crypto.json` | `ef0531ae152108fe30717c2b3136749f80de59bdcb86466d705657269c7f7fb8` |
| `backend/knowledge/us.json` | `bf9acad6e3fc7b613fdb75e7696dd78ae4816a57f8367d5acb1584838d02e420` |
| `backend/scripts/run_final_test.py` | `1244d6451f5e869c7f98d11c88b29cc132f603b1c1de198fea466be7bbc072c3` |
| `backend/scripts/run_rule_baselines.py` | `1af47b56ac3f54391b0b317aad77ea24845f893d0ba8aa977f5ebe21e9b69e43` |
| `backend/scripts/run_validation_experiment.py` | `ad5e196204d3d5d8aa262e0934524f1330ba8a19af972992e93ec7a4be9e1acf` |

---

## 4. Accuracy Prior Choice

**Choice: neutral prior (0.5 for every market).**

Rationale: A warm-start from the learning window would require running all four modes
across 2022–2024 to build prior accuracy, then handing that prior to the test run. This
couples the learning window to the final number and makes the protocol harder to audit.
Starting from a neutral prior is simpler, verifiable, and conservative: the agents earn
their weights entirely within the evaluation run.

The prior is stored as `accuracy_prior: 0.5` in `markets.yaml` and read by
`AccuracyTracker` on construction. Changing it requires updating `markets.yaml` and
re-hashing the freeze table above.

---

## 5. Mode Definitions (Part 0.2)

| Mode enum | Weighting | Dialogue |
|---|---|---|
| `SINGLE` | n/a (target only) | None |
| `SILENT_UNWEIGHTED` | Equal votes (weight = 1.0, no role, no accuracy) | None |
| `SILENT` / `SILENT_WEIGHTED` | role × learned accuracy | None |
| `DEBATE` | role × learned accuracy (same as weighted) | 3-round structured dialogue |

The comparison experiment runs all four modes on the validation window, then again (once)
on the test window. Results for target=US and target=CRYPTO are reported separately and
never averaged.

---

## 6. Evaluation Day Counts (from BarByBarSimulator)

- **Evaluation days (test window):** 474 — US trading days where both SPY and BTC have
  valid candles at the 16:00 ET cutoff.
- **Degraded days:** 215 — days where one or both markets lack data (NYSE holidays,
  weekends). Excluded from main metrics; counted and reported separately.

Fill rules:
- SPY: next US trading day's open.
- BTC: open of the first 1h candle at the 21:00 UTC cutoff.

---

## 7. SPY Data Status

- Rows: 1,227 trading days (2022-01-03 to 2026-11-20).
- SHA-256 of the raw file: `c617dbb50402e607d9a3fa136a5f75b24065f0e772341a7fabb4a2b87211131a`
- SHA-256 with CRLF normalised to LF (the value in section 3): `cf84eb64b842aa10198809ec147cfe3fef49c7fd9a19429a7a257daa6dd828e5`. Same file, two line-ending treatments.
- One correction applied (Part A): 2025-05-22 stale row replaced from Nasdaq crosscheck.
  See `backend/data_cache/SPY_CORRECTIONS.md` for full audit trail.
- Prices are **unadjusted raw** (no dividend/split adjustment).

## 8. BTC Data Status

- Rows: 42,791 hourly candles (2022-01-03 00:00 UTC to 2026-11-20 23:00 UTC).
- SHA-256 of the raw file: `9ee5cce53336453b325509bfe5ca3a7bfbc1ab545a000812aac059f0be426e40`
- SHA-256 with CRLF normalised to LF (the value in section 3): `3dddb0563c3362f3ee1e21e7ded9542f8b1b4ae344bb20bb89c0e8c59c2c7feb`. Same file, two line-ending treatments.
- One missing hour: 2023-03-24 13:00 UTC (Binance matching engine outage, real event).
  No correction applied; gap is documented and within the learning window.

---

## 9. Session IDs

The old format ended in a short random hex suffix taken from `uuid.uuid4().hex`. The new format
is `QRM-{year}-` followed by the full 32 hex characters.

---

## 10. Risk Veto Semantics

Three distinct behaviours after the `RiskLayer.evaluate` call:

| Scenario | `RiskStatus` | `veto_source` | Simulator behaviour |
|---|---|---|---|
| Consensus HOLD or ABSTAIN | `APPROVED` | `""` | Keep current position; no trade. |
| Drawdown breach | `OVERRIDDEN` | `"drawdown"` | Flatten position (force close); block new entries for `DRAWDOWN_COOLOFF_DAYS` more days. |
| Volatility breach | `OVERRIDDEN` | `"volatility"` | Override BUY/SELL to HOLD; no position change forced. |

**Cool-off re-arm rule:**  
On a drawdown breach day the replay simulator sets `cooloff_remaining = drawdown_cooloff_days`
(per target: `DRAWDOWN_COOLOFF_DAYS_BY_TARGET`, US 5 and CRYPTO 20, in `settings.py`).  On each subsequent day while
`cooloff_remaining > 0`, the final action is overridden to HOLD, drawdown is not
re-evaluated, and the counter is decremented.  When it reaches 0 the breaker re-arms:
**the equity peak is rebased to current equity** and normal signals resume.  The 5%
limit is therefore measured from the last re-arm, not from the all-time peak, so total
drawdown over a run can exceed 5% through repeated breaches.

Before this fix the peak was never reset, so the breaker re-tripped every day, reset the
counter, and stayed locked for the rest of the run.

**HOLD keeps the position.** The simulator was changed to match this section. The choice was
made for consistency with this protocol, not for returns.

**Cool-off selection criterion (written before the grid below is re-run):**
for each target separately, choose from {1, 3, 5, 10, 20} the value with the lowest mean
maximum drawdown across the four modes (single, silent_unweighted, silent_weighted, debate)
on the validation window (2024). Ties go to the shorter cool-off. No return or Sharpe figure
is used. This replaces the earlier mean-Sharpe rule. Values and results are in
`breaker_and_debate.md`.

---

## 11. HOLD scoring

HOLD calls are **excluded** from accuracy updates. Rationale: HOLD carries no directional
conviction, so scoring it as correct (realised_return==0 is rare) or incorrect would add
noise. Only BUY and SELL calls update the tracker. ABSTAIN and non-VALID calls are also
excluded (see Part 0.1).

---

## 12. Debate volatility thresholds (written before the run that uses them)

The fixed debate volatility thresholds (challenge > 2.0, reply > 2.4, final stance > 2.0) are
replaced, for each agent, by that agent's **own 90th percentile** of its volatility measure
(std of the last 14 log returns of its own candles at each decision cutoff) on the
**learning window (2022-01-03 to 2023-12-31) only**. All three thresholds of an agent take
that one value. The values are computed by `scripts/compute_debate_thresholds.py` and stored in
`app/config/debate_thresholds.json`. RSI thresholds and the risk-layer limits are unchanged.

**Reason:** the original numbers are daily-scale, while the CRYPTO agent measures hourly
volatility.

**Disclosure:** this was decided **after** seeing the validation (2024) result in which debate
never changed a decision. It is therefore not a pre-registered rule, and 2024 debate results are
not independent evidence for it. The original-threshold run is kept as an ablation. Nothing else
is changed after seeing the new result.

---

## 13. Final Test Run (written before it is run)

Validation used knowledge learned from 2022-2023; the test run uses 2022-2024.

**Knowledge check (before the run):** `build_learning_window_knowledge.py` filters both CSVs to
2022-01-03 .. 2024-12-31 before computing anything. It was also rerun on copies of the CSVs
physically cut at 2024-12-31 (SPY 753 rows, last 2024-12-31; BTC 26,255 hourly rows, last bar
opening 2024-12-31 23:00 UTC). Both outputs were identical to `knowledge/us.json` and
`knowledge/crypto.json`.

- (a) For the test run the learned debate thresholds are recomputed on **2022-01-03 to
  2024-12-31** by the same 90th-percentile rule (`compute_debate_thresholds.py --test-run`,
  stored in `app/config/debate_thresholds_test.json`). Pattern knowledge is
  `backend/knowledge/` (2022-2024). The cool-off lengths **stay as chosen on validation**.
- (b) The earlier test-window run is **void** (section 1). The run of
  `scripts/run_final_test.py --final-test` is the **only counted** test run.
- (c) Bugs found after the test run are recorded as **errata** next to the results. The run
  is not silently repeated.

The script writes `docs/status/FINAL_TEST.lock` (start, then finish or failure status) and
writes results only at the end, through a renamed temporary file. If it fails for a non-result
reason (a missing file, a path error), deleting the lock and rerunning is allowed, and **must** be
recorded as an erratum with the reason. It refuses to run if the lock
exists or if any frozen file differs from the table in section 3. Unit tests of the data
adapters do read candles dated inside the test window; they compute no returns or decisions.

---

## 14. Changes Between and After the Freeze Tags

| Commit | Change | Effect on computed numbers |
|---|---|---|
| `317e0e0` (after v1) | `run_wp4_experiment.py` limited to 2024, one new test, protocol sections 2, 7, 8, 9, 13 | None: no file in the section 3 table changed. |
| `ce31888` (after v1) | List of post-tag commits | None: documentation only. |
| the commit tagged `rules-freeze-v2` | `run_final_test.py`: atomic results write, lock status; tests; its hash row | None: only how results are saved. A 2024 rehearsal gave identical tables before and after. |

`rules-freeze-v1` remains in history. No test-window run was made under it.
