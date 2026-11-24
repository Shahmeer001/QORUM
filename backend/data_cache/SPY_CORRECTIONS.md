# SPY Daily Data Validation & Quality Audit Report
**Dataset**: `backend/data_cache/spy_daily.csv`
**Rows Analyzed**: 1227 rows
**Date Range**: 2022-01-03 to 2026-11-20
**Last Validated**: Part A audit (correctness pass)

---

## 1. Summary of Integrity Checks

| Quality Check | Result | Details |
| :--- | :--- | :--- |
| **Missing / Null Values** | **PASS (0)** | Zero nulls across all 6 columns |
| **OHLC Logic Consistency** | **PASS (0)** | High ≥ Low, High ≥ Open/Close, Low ≤ Open/Close |
| **Weekend Ingestion** | **PASS (0)** | Zero Saturday or Sunday bars |
| **Duplicate Timestamps** | **PASS (0)** | Every trading date is unique |
| **Non-Positive Prices** | **PASS (0)** | All prices strictly positive |
| **Non-Positive Volume** | **PASS (0)** | All volume values strictly positive |
| **Extended Market Gaps (>4 days)** | **PASS (0)** | All gaps align with standard NYSE holidays |
| **Extreme 1-Day Moves (>10%)** | **1 Incident** | 2025-04-09 (+10.50% gain) — real, kept |

---

## 2. Corrections Applied

### Correction 1 — 2025-05-22 Stale Row (FIXED)
- **Problem**: The row for 2025-05-22 was an exact copy of 2025-05-21 (same OHLCV). The Volume of 2,169,841 was implausibly low for SPY on a normal trading day.
- **Source of correction**: `spy_daily_crosscheck.csv` (Nasdaq feed, MM/DD/YYYY format), which shows the real values for 2025-05-22.
- **Corrected values** (from crosscheck):
  - Open: 582.66 → *(was 588.44)*
  - High: 586.62 → *(was 592.58)*
  - Low: 581.405 → *(was 581.82)*
  - Close: 583.09 → *(was 582.86)*
  - Volume: 70,860,420 → *(was 2,169,841)*
- **SHA-256 after correction**: `c617dbb50402e607d9a3fa136a5f75b24065f0e772341a7fabb4a2b87211131a`

### Finding 2 — 2026-04-20 Crosscheck Placeholder (NOT corrected)
- The crosscheck file has O=H=L=C=710.14 and V=NaN for 2026-04-20 — this is a placeholder stub (Apr 17 close copied into Apr 20 by the Nasdaq feed, likely due to Easter Monday market ambiguity in their system).
- **The SPY dataset row for 2026-04-20 is consistent and correct**: O=708.78, H=709.91, L=706.14, C=708.72, V=43,546,812 — plausible normal trading day, all OHLC constraints satisfied.
- **Action**: No correction applied. The XC placeholder is itself wrong; the SPY row is kept as-is.

### Finding 3 — 2026-04-17 Crosscheck Volume Filler
- The crosscheck shows V=9,999,999 for 2026-04-17 — a known Nasdaq data-feed placeholder.
- The SPY dataset shows V=70,661,927, which is plausible. No correction needed.

---

## 3. Notes on Raw Pricing
- All prices in `spy_daily.csv` are **unadjusted raw prices** (no dividend or split adjustment). This is intentional; adjustments would create look-ahead contamination because they are applied retroactively.

---

## 4. 2025-04-09 Large Move
- Date: 2025-04-09
- Move: +10.50% (Open=493.44, Close=548.62)
- Status: **Real historical event** — the largest single-day SPY gain in the test window, coinciding with a sharp macro reversal. Kept intact to preserve raw price history.
