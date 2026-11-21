# QUORUM Research Pipeline

This directory contains the complete quantitative research methodology and empirical data pipeline that produces pattern statistics and baseline models for QUORUM market agents.

## Execution Order

The scripts must be executed sequentially from `01` to `07`:

1. **`01_download_data.py`**
   - Fetches historical BTC/USDT 5-minute OHLCV candles from Binance (frozen 1-year historical window).
   - Generates `output/btc_ohlcv.csv` and `output/data_meta.json`.

2. **`02_random_dummy_trades.py`**
   - Simulates 40,000 baseline trades with random holding periods (15m to 10d).
   - Establishes statistical benchmarks for win rate and ROI.
   - Generates `output/dummy_trades_random.csv`.

3. **`03_roi_and_indicators.py`**
   - Computes RSI (14-period), Volume, Liquidity, and relative measures across trades.
   - Tags high-profit (+10% ROI) and large-loss (-10% ROI) outcomes.
   - Generates `output/trades_with_roi_and_indicators.csv`.

4. **`04_pattern_stats.py`**
   - Labels 3-candle and 7-candle price movement patterns (U = Up, S = Same, D = Down).
   - Tests pattern profitability and stability across data splits.
   - Emits `output/agent_pattern_knowledge.json` for agent ingestion.

5. **`05_rsi_strategy.py`**
   - Implements Method 2: Systematic RSI-based entry (20-30 zone) and exit (70-80 zone).
   - Outputs `output/strategy_rsi_trades.csv` and `output/strategy_rsi_summary.csv`.

6. **`06_make_report.py`**
   - Synthesizes findings into `output/QUORUM_report.pdf` and summary visuals.

7. **`07_profitable_pattern_histograms.py`**
   - Generates frequency histograms of candle patterns preceding profitable trades.
   - Outputs `output/supervisor_histograms/` and `output/supervisor_histograms/Profitable_pattern_histograms.pdf`.
