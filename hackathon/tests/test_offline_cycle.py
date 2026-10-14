"""Verify the synthetic CLI mode has no external service side effects."""
from datetime import datetime

import numpy as np
import main
from api_client import client


def test_offline_cycle_never_fetches_or_submits(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("simulation must never call market APIs")
    monkeypatch.setattr(client, "_make_request", forbidden)
    monkeypatch.setattr(main, "get_prices", forbidden)
    monkeypatch.setattr(main, "get_inventory", forbidden)
    monkeypatch.setattr(main, "submit_bid", forbidden)
    np.random.seed(7)
    result = main.run_gridpilot_gt(simulate=True)
    assert result["success"] and result["mode"] == "synthetic-simulation"
    assert result["constraints_satisfied"]
    assert 0 <= result["total_power"] <= 1000
    assert np.isfinite(result["total_power"])


def test_default_inventory_uses_one_megawatt_in_kw(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    inventory = client._generate_fallback_inventory()
    assert inventory["power_total"] == 1000
    assert inventory["power_used"] + inventory["power_available"] == 1000


def test_seed_and_as_of_are_independent_of_wall_clock(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    class Morning(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 13, 1, 0, 0, tzinfo=tz)

    class Afternoon(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 13, 12, 0, 0, tzinfo=tz)

    monkeypatch.setattr(client, "datetime", Morning)
    morning = main.build_offline_receipt(
        main.run_gridpilot_gt(
            simulate=True,
            seed=8257,
            as_of="2026-10-13T00:00:00Z",
        )
    )

    monkeypatch.setattr(client, "datetime", Afternoon)
    afternoon = main.build_offline_receipt(
        main.run_gridpilot_gt(
            simulate=True,
            seed=8257,
            as_of="2026-10-13T00:00:00Z",
        )
    )

    assert morning == afternoon
