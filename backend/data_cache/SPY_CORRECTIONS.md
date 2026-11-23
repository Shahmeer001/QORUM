# SPY Daily Data Validation & Quality Audit Report
**Dataset**: `backend\data_cache\spy_daily.csv`  
**Rows Analyzed**: 1227 rows  
**Date Range**: 2022-01-03 to 2026-11-20  

---

## 1. Summary of Integrity Checks

| Quality Check | Result | Details |
| :--- | :--- | :--- |
| **Missing / Null Values** | **PASS (0)** | Zero nulls across all 6 columns |
| **OHLC Logic Consistency** | **PASS (0)** | High >= Low, High >= Open/Close, Low <= Open/Close |
| **Weekend Ingestion** | **PASS (0)** | Zero Saturday or Sunday bars ingested |
| **Duplicate Timestamps** | **PASS (0)** | Every trading date is unique |
| **Non-Positive Prices** | **PASS (0)** | All prices strictly positive |
| **Non-Positive Volume** | **PASS (0)** | All volume values strictly positive |
| **Extended Market Gaps (>4 days)** | **PASS (0)** | All gaps align with standard 1-3 day weekend/exchange holidays |
| **Extreme 1-Day Moves (>10%)** | **1 Incident** | 2025-04-09 (+10.50% gain) |

---

## 2. Identified Anomalies & Corrections

1. **Extreme 1-Day Volatility Event**:
   - Date: `2025-04-09`
   - Move: `+10.50%` following previous decline.
   - Status: Kept intact as raw price history to avoid synthetic smoothing or survivorship distortion.
2. **Raw Pricing Note**:
   - The prices in `spy_daily.csv` represent unadjusted raw prices (no dividend/split adjustment).

---

## 3. Data Corrections Applied
- **Date format parsing**: Explicit day-first parsing (`format="%d/%m/%Y"`) enforced in `USMarketAdapter`.
- **Trading date membership**: `USMarketAdapter` restricts valid candles strictly to dates in `spy_daily.csv` to automatically discard US exchange holidays.
