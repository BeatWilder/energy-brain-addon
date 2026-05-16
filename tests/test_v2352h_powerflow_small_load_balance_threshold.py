from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_plain_status,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_small_load_battery_help_does_not_also_show_grid_import():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.3,
                "battery_kw": -0.3,
                "grid_kw": 0.3,
            },
            "battery_soc_card": {"soc_percent": 79.2},
            "planner_timeline": [{"soc_percent": 78.1}],
        }
    )

    assert snapshot["grid_raw_kw"] == 0.3
    assert snapshot["grid_balanced_kw"] == 0.0
    assert snapshot["grid_balance_corrected"] is True
    assert snapshot["grid_kw"] == 0.0
    assert snapshot["grid_balance_threshold_kw"] <= 0.1


def test_small_load_plain_text_says_net_bijna_nul():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.3,
                "battery_kw": -0.3,
                "grid_kw": 0.3,
            },
            "battery_soc_card": {"soc_percent": 79.2},
            "planner_timeline": [{"soc_percent": 78.1}],
        }
    )

    plain = powerflow_plain_status(snapshot)

    assert "Batterij helpt het huis met 0.3 kW" in plain["headline"]
    assert "Het net vult nog 0.3 kW bij" not in plain["headline"]
    assert "bijna geen netverbruik" in plain["headline"]
    assert plain["grid_badge"] == "Net bijna nul · gebalanceerd"


def test_small_load_render_does_not_show_wrong_net_vult_bij():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.3,
                "battery_kw": -0.3,
                "grid_kw": 0.3,
            },
            "battery_soc_card": {"soc_percent": 79.2},
            "planner_timeline": [{"soc_percent": 78.1}],
        }
    )

    html = render_powerflow_svg(snapshot, [])

    assert "Net vult bij: 0.3 kW" not in html
    assert "Net bijna nul · gebalanceerd" in html
    assert "netwaarde gebalanceerd voor weergave" in html


def test_tiny_meter_jitter_is_not_overcorrected():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.3,
                "battery_kw": -0.3,
                "grid_kw": 0.04,
            },
            "battery_soc_card": {"soc_percent": 79.2},
        }
    )

    assert snapshot["grid_balance_corrected"] is False
    assert snapshot["grid_kw"] == 0.0
