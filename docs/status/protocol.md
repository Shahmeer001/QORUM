# QUORUM Evaluation Protocol
**Project:** QUORUM — Governed Multi-Agent Decision Engine (FYP1)
**Status:** Preliminary (FYP1) — rules frozen at tag `rules-freeze-v1` (pending creation)

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
| Learning | 2022-01-03 – 2024-12-31 | Build pattern knowledge (`us.json`, `crypto.json`) |
| Validation | 2024-01-01 – 2024-12-31 | Parameter selection, rule tuning, mode comparison |
| Test (held-out) | 2025-01-01 – 2026-11-20 | Looked at **exactly once**, from the frozen tag |

> **Rule**: All development (rule thresholds, min_margin, risk limits, signal weights) must be
> chosen on the validation split only. The test window is opened once, at the end, and the
> numbers reported are final.

---

## 3. Rules-Freeze Protocol

Before the final test run, create the git tag:

```
git tag rules-freeze-v1
git push origin rules-freeze-v1
```

The frozen files and their SHA-256 hashes at the time of freeze are recorded below.
These are the **current** hashes (HEAD `a02335e`); update this table when the tag is created.

| File | SHA-256 |
|---|---|
| `backend/app/agents/brains/rule_brain.py` | `31bb55417ea9b1ca6cdc84ff40d794260d94cdccdd71584f53134f1b36533174` |
| `backend/app/risk/risk_layer.py` | `074c2312c1b721cc5a3bf7b62ceac266201f83e03c0b8f867c51ec5da3f3c7b9` |
| `backend/app/risk/rules.py` | `512388cb67db5ced725c5fccb0199e43fec88106dd8544e69c7a31e254e2e938` |
| `backend/app/config/settings.py` | `19d14545139c4158c746faf35ba6da64059b2fb56176b57888acc1f50b2aca99` |
| `backend/app/config/markets.yaml` | `f8507820c61f9cf5ae4854e502dc0dee4ad21bdc0ca81c333ebef8ff471b0158` |
| `backend/knowledge/us.json` | `2218c24d130f46ddd2ea1721865ae31eff3e6e5f89b2d498f358f61571d1c067` |
| `backend/knowledge/crypto.json` | `f85094d6b1fe4563d91c8606ac8b3ec08a21970ea5bc8c95ba56d5b122924675` |

Verification command (run from repo root):

```powershell
@'
import hashlib, pathlib
files = [
    "backend/app/agents/brains/rule_brain.py",
    "backend/app/risk/risk_layer.py",
    "backend/app/risk/rules.py",
    "backend/app/config/settings.py",
    "backend/app/config/markets.yaml",
    "backend/knowledge/us.json",
    "backend/knowledge/crypto.json",
]
for f in files:
    h = hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
    print(f"{h}  {f}")
'@ | python -
```

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
- SHA-256: `c617dbb50402e607d9a3fa136a5f75b24065f0e772341a7fabb4a2b87211131a`
- One correction applied (Part A): 2025-05-22 stale row replaced from Nasdaq crosscheck.
  See `backend/data_cache/SPY_CORRECTIONS.md` for full audit trail.
- Prices are **unadjusted raw** (no dividend/split adjustment).

## 8. BTC Data Status

- Rows: 42,791 hourly candles (2022-01-03 00:00 UTC to 2026-11-20 23:00 UTC).
- SHA-256: `9ee5cce53336453b325509bfe5ca3a7bfbc1ab545a000812aac059f0be426e40`
- One missing hour: 2023-03-24 13:00 UTC (Binance matching engine outage, real event).
  No correction applied; gap is documented and within the learning window.

---

## 9. Session IDs

Format: `QRM-{year}-{uuid4().hex}` — 32 hex chars from `uuid.uuid4().hex`, prefixed with
`QRM-{year}-`.  Example: `QRM-2026-3f4e8a1b2c5d6e7f8a9b0c1d2e3f4a5b`.

**What the `_build_summaries(session_id)` bug was:**  
The old format used only 3 uppercase hex chars (`uuid.uuid4().hex[:8].upper()` → 8 chars,
but the concern is that only 4096 total combinations existed with 3 lowercase hex chars in
an earlier incarnation). Two concurrent sessions in the same process could collide;
if two sessions shared an ID, `_build_summaries` would have called
`self.board.get_all("")` (the wrong key) and read messages from the wrong session,
producing incorrect initial positions or silently skipping messages.

**Why no silent cross-contamination in practice:**  
The `MemoryBoardRepository` stores messages keyed by `session_id`. With the old short
suffix, a collision would have caused a duplicate-key error on SQLite insert (the
`sessions` table uses `session_id` as a primary key), not silent data mixing. The fix
uses `uuid.uuid4().hex` (32 chars), making collisions astronomically unlikely, and passes
`session_id` explicitly to all board calls.

---

## 10. Risk Veto Semantics

Three distinct behaviours after the `RiskLayer.evaluate` call:

| Scenario | `RiskStatus` | `veto_source` | Simulator behaviour |
|---|---|---|---|
| Consensus HOLD | `APPROVED` | `""` | Keep current position; no trade. |
| Drawdown breach | `OVERRIDDEN` | `"drawdown"` | Flatten position (force close); block new entries for `DRAWDOWN_COOLOFF_DAYS` more days. |
| Volatility breach | `OVERRIDDEN` | `"volatility"` | Override BUY/SELL to HOLD; no position change forced. |

**Cool-off re-arm rule:**  
On a drawdown breach day the replay simulator sets `cooloff_remaining = drawdown_cooloff_days`
(default: `DRAWDOWN_COOLOFF_DAYS = 10`, in `settings.py`).  On each subsequent day while
`cooloff_remaining > 0`, the final action is overridden to HOLD and the counter is
decremented.  When it reaches 0 the breaker re-arms and normal signals resume.

The parameter `DRAWDOWN_COOLOFF_DAYS = 10` was chosen as the initial value and may be
tuned on the validation split (2024).

---

## 11. HOLD scoring

HOLD calls are **excluded** from accuracy updates. Rationale: HOLD carries no directional
conviction, so scoring it as correct (realised_return==0 is rare) or incorrect would add
noise. Only BUY and SELL calls update the tracker. ABSTAIN and non-VALID calls are also
excluded (see Part 0.1).
