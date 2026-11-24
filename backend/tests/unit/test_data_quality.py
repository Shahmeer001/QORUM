"""
Tests for the SPY data quality checks (task 2 / A3).

Runs run_quality_checks() against:
  - A clean fixture (all checks pass)
  - Targeted bad fixtures, one defect per check

No test-window data is loaded. All fixtures are synthetic.
"""
from __future__ import annotations

import pandas as pd
import pytest

# Import the check function directly from the script
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from validate_spy_data import run_quality_checks


def _df(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal DataFrame in the shape validate_spy_data expects."""
    df = pd.DataFrame(rows)
    df["dt"] = pd.to_datetime(df["dt"])
    return df


# ---------------------------------------------------------------------------
# Helpers — one clean row and one per defect
# ---------------------------------------------------------------------------
CLEAN_ROW = dict(dt="2024-01-02", Open=400.0, High=410.0, Low=395.0, Close=405.0, Volume=50_000_000)


def _clean(n: int = 3) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append(dict(
            dt=f"2024-01-0{i+2}",
            Open=400.0 + i,
            High=410.0 + i,
            Low=395.0 + i,
            Close=405.0 + i,
            Volume=50_000_000,
        ))
    return _df(rows)


# ---------------------------------------------------------------------------
# (1) Clean fixture — all checks pass
# ---------------------------------------------------------------------------
def test_clean_fixture_passes_all_checks():
    findings = run_quality_checks(_clean(5))
    for key, issues in findings.items():
        assert issues == [], f"Expected no issues for '{key}', got {issues}"


# ---------------------------------------------------------------------------
# (2) Zero-volume bar
# ---------------------------------------------------------------------------
def test_detects_zero_volume_bar():
    df = _clean(3)
    df.loc[1, "Volume"] = 0
    findings = run_quality_checks(df)
    assert len(findings["zero_volume"]) == 1
    assert findings["zero_volume"][0]["Volume"] == 0


# ---------------------------------------------------------------------------
# (3) Consecutive identical rows
# ---------------------------------------------------------------------------
def test_detects_consecutive_identical_rows():
    df = _clean(4)
    # Make row 2 an exact copy of row 1
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df.loc[2, col] = df.loc[1, col]
    findings = run_quality_checks(df)
    assert len(findings["consecutive_identical"]) == 1


# ---------------------------------------------------------------------------
# (4) High < Low (OHLC inversion)
# ---------------------------------------------------------------------------
def test_detects_high_lt_low():
    df = _clean(3)
    df.loc[1, "High"] = 390.0   # below Low=395
    findings = run_quality_checks(df)
    assert len(findings["high_lt_low"]) == 1


# ---------------------------------------------------------------------------
# (5) Close outside [Low, High]
# ---------------------------------------------------------------------------
def test_detects_close_above_high():
    df = _clean(3)
    df.loc[1, "Close"] = 420.0  # above High=410
    findings = run_quality_checks(df)
    assert len(findings["close_outside_range"]) == 1


def test_detects_close_below_low():
    df = _clean(3)
    df.loc[1, "Close"] = 390.0  # below Low=395
    findings = run_quality_checks(df)
    assert len(findings["close_outside_range"]) == 1


# ---------------------------------------------------------------------------
# (6) Open outside [Low, High]  (extra check in validate_spy_data)
# ---------------------------------------------------------------------------
def test_detects_open_outside_range():
    df = _clean(3)
    df.loc[1, "Open"] = 420.0  # above High=410
    findings = run_quality_checks(df)
    assert len(findings["open_outside_range"]) == 1


# ---------------------------------------------------------------------------
# (7) Real file: corrected spy_daily.csv must pass all checks
# ---------------------------------------------------------------------------
def test_real_spy_file_passes_all_checks():
    spy_path = Path(__file__).resolve().parents[2] / "data_cache" / "spy_daily.csv"
    if not spy_path.exists():
        pytest.skip("spy_daily.csv not present")
    df = pd.read_csv(spy_path)
    df["dt"] = pd.to_datetime(
        df["Date"].astype(str).str.split().str[0], format="%d/%m/%Y"
    )
    df = df.sort_values("dt").reset_index(drop=True)
    findings = run_quality_checks(df)
    for key, issues in findings.items():
        assert issues == [], f"Real spy_daily.csv failed check '{key}': {issues}"
