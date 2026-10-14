"""Subprocess coverage for the documented provider-free command."""

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def run_demo(receipt: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "main.py",
            "--mode",
            "gridpilot",
            "--simulate",
            "1",
            "--seed",
            "8257",
            "--as-of",
            "2026-10-13T00:00:00Z",
            "--receipt",
            str(receipt),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_root_entrypoint_runs_and_receipt_is_deterministic(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    first_run = run_demo(first)
    second_run = run_demo(second)

    assert first_run.returncode == 0, first_run.stderr
    assert second_run.returncode == 0, second_run.stderr
    assert "SIMULATION - Would submit payload" in first_run.stdout
    assert "GridPilot-GT executed successfully" in first_run.stdout
    assert first.read_bytes() == second.read_bytes()

    receipt = json.loads(first.read_text(encoding="utf-8"))
    assert receipt["schema"] == "gridpilot.offline-receipt.v1"
    assert receipt["mode"] == "synthetic-simulation"
    assert receipt["seed"] == 8257
    assert receipt["as_of"] == "2026-10-13T00:00:00Z"
    assert receipt["constraints_satisfied"] is True
    assert receipt["scope"] == "provider-free synthetic fixture; no market submission"
    assert 0 < receipt["metrics"]["total_power_kw"] <= 1000


def test_live_mode_refuses_offline_receipt(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--mode",
            "gridpilot",
            "--simulate",
            "0",
            "--receipt",
            str(tmp_path / "must-not-exist.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 2
    assert "--receipt is available only with --simulate 1" in completed.stderr
