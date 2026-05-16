from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_plain_status,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_powerflow_plain_status_explains_import_and_battery_help():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": -1.705,
                "grid_kw": 1.71,
                "load_kw": 4.027,
                "pv_kw": 2.322,
            },
            "battery_soc_card": {"soc_percent": 88.8},
            "planner_timeline": [{"soc_percent": 84.313158}],
        }
    )

    plain = powerflow_plain_status(snapshot)

    assert "Huis gebruikt 4.0 kW" in plain["headline"]
    assert "Zon levert 2.3 kW" in plain["headline"]
    assert "Batterij helpt het huis met 1.7 kW" in plain["headline"]
    assert "Het net vult nog 1.7 kW bij" in plain["headline"]
    assert plain["battery_badge"] == "Helpt huis: 1.7 kW"
    assert plain["grid_badge"] == "Net vult bij: 1.7 kW"
    assert "Batterij nu 88.8%" in plain["soc"]
    assert "Planner stap 0 rekent met 84.3%" in plain["soc"]


def test_powerflow_plain_status_explains_battery_charging_and_export():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": 2.0,
                "grid_kw": -0.5,
                "load_kw": 1.0,
                "pv_kw": 3.5,
            },
            "battery_soc_card": {"soc_percent": 62.0},
            "planner_timeline": [{"soc_percent": 62.0}],
        }
    )

    plain = powerflow_plain_status(snapshot)

    assert "Batterij wordt geladen met 2.0 kW" in plain["headline"]
    assert "Er gaat 0.5 kW terug naar het net" in plain["headline"]
    assert plain["battery_badge"] == "Laden: 2.0 kW"
    assert plain["grid_badge"] == "Teruglevering: 0.5 kW"
    assert plain["soc"] == "Batterij nu 62.0%."


def test_compact_powerflow_render_contains_plain_sections_not_scattered_labels():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": -1.705,
                "grid_kw": 1.71,
                "load_kw": 4.027,
                "pv_kw": 2.322,
            },
            "battery_soc_card": {"soc_percent": 88.8},
            "planner_timeline": [{"soc_percent": 84.313158}],
        }
    )
    html = render_powerflow_svg(snapshot, [])

    assert "compact-powerflow" in html
    assert "powerflow-plain" in html
    assert "powerflow-summary-grid" in html
    assert "Waar komt de stroom nu vandaan" in html
    assert "89% nu" in html
    assert "Batterij nu 88.8%" in html
    assert "Planner stap 0 rekent met 84.3%" in html
    assert "Zon naar huis:" not in html
    assert "Import uit net:" not in html
