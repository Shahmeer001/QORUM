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
