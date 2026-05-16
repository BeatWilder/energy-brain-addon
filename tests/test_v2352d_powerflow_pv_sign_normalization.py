from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_plain_status,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_powerflow_normalizes_negative_pv_sign_for_display():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": 0.0,
                "grid_kw": 9.11,
                "load_kw": 1.111,
                "pv_kw": -8.0,
            },
            "battery_soc_card": {"soc_percent": 88.8},
        }
    )

    assert snapshot["pv_raw_kw"] == -8.0
    assert snapshot["pv_kw"] == 8.0
    assert snapshot["pv_sign_normalized"] is True
    assert "PV teken genormaliseerd" in snapshot["data_quality"]


def test_powerflow_plain_status_never_says_zon_levert_negative_kw():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": 0.0,
                "grid_kw": 9.11,
                "load_kw": 1.111,
                "pv_kw": -8.0,
            },
            "battery_soc_card": {"soc_percent": 88.8},
        }
    )

    plain = powerflow_plain_status(snapshot)

    assert "Zon levert -8.0 kW" not in plain["headline"]
    assert "Zon levert 8.0 kW" in plain["headline"]
    assert "PV-teken is genormaliseerd" in plain["headline"]


def test_powerflow_svg_marks_normalized_pv_without_negative_display():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": 0.0,
                "grid_kw": 9.11,
                "load_kw": 1.111,
                "pv_kw": -8.0,
            },
            "battery_soc_card": {"soc_percent": 88.8},
        }
    )

    html = render_powerflow_svg(snapshot, [])

    assert "Zon levert -8.0 kW" not in html
    assert ">8.0 kW<" in html
    assert "Stroomrichting - live/schaduwdata · PV teken genormaliseerd" in html
    assert "PV-teken is genormaliseerd" in html
