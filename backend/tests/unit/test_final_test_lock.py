"""The test window can be opened only with --final-test and only once.
run_experiment is always stubbed here: these tests never touch real data windows."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import run_final_test as ft


@pytest.fixture
def calls(monkeypatch):
    made = []
    monkeypatch.setattr(ft, "run_experiment", lambda *a: made.append(a))
    monkeypatch.setattr(ft, "frozen_mismatches", lambda text: [])
    return made


def test_requires_flag_and_creates_no_lock(tmp_path, calls):
    with pytest.raises(SystemExit, match="--final-test"):
        ft.main([], lock_path=tmp_path / "x.lock")
    assert not calls and not (tmp_path / "x.lock").exists()


def test_second_run_is_refused(tmp_path, calls):
    lock = tmp_path / "x.lock"
    ft.main(["--final-test"], lock_path=lock)
    first = lock.read_text()
    assert "final test started 20" in first
    with pytest.raises(SystemExit, match="lock file exists"):
        ft.main(["--final-test"], lock_path=lock)
    with pytest.raises(SystemExit, match="lock file exists"):
        ft.acquire_lock(lock)
    assert len(calls) == 1 and lock.read_text() == first


def test_changed_frozen_file_blocks_run_without_locking(tmp_path, calls, monkeypatch):
    monkeypatch.setattr(ft, "frozen_mismatches", lambda text: ["backend/app/x.py"])
    with pytest.raises(SystemExit, match="freeze table"):
        ft.main(["--final-test"], lock_path=tmp_path / "x.lock")
    assert not calls and not (tmp_path / "x.lock").exists()
