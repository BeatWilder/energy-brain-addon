from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_plain_status,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_powerflow_corrects_impossible_grid_import_when_battery_covers_house():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 1.4,
                "battery_kw": -1.4,
                "grid_kw": 1.4,
            },
            "battery_soc_card": {"soc_percent": 82.8},
        }
    )

    assert snapshot["grid_raw_kw"] == 1.4
    assert snapshot["grid_balanced_kw"] == 0.0
    assert snapshot["grid_kw"] == 0.0
    assert snapshot["grid_balance_corrected"] is True
    assert "netwaarde gebalanceerd voor weergave" in snapshot["data_quality"]


def test_powerflow_plain_status_does_not_claim_grid_import_after_balance_fix():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 1.4,
                "battery_kw": -1.4,
                "grid_kw": 1.4,
            },
            "battery_soc_card": {"soc_percent": 82.8},
        }
    )

    plain = powerflow_plain_status(snapshot)

    assert "Batterij helpt het huis met 1.4 kW" in plain["headline"]
    assert "Het net vult nog 1.4 kW bij" not in plain["headline"]
    assert "bijna geen netverbruik" in plain["headline"]
    assert "gebalanceerde weergave" in plain["headline"]


def test_powerflow_svg_shows_balanced_grid_and_warning_not_wrong_import():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 1.4,
                "battery_kw": -1.4,
                "grid_kw": 1.4,
            },
            "battery_soc_card": {"soc_percent": 82.8},
        }
    )

    html = render_powerflow_svg(snapshot, [])

    assert "Net vult bij: 1.4 kW" not in html
    assert "Net bijna nul" in html
    assert "netwaarde gebalanceerd voor weergave" in html
    assert "gebalanceerde weergave" in html


def test_powerflow_keeps_consistent_grid_import_unchanged():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 1.4,
                "battery_kw": 0.0,
                "grid_kw": 1.4,
            },
            "battery_soc_card": {"soc_percent": 82.8},
        }
    )

    assert snapshot["grid_kw"] == 1.4
    assert snapshot["grid_raw_kw"] == 1.4
    assert snapshot["grid_balance_corrected"] is False
