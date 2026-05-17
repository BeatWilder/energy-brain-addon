from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import render_tesla_cockpit_html


def test_v2352r_powerflow_card_space_is_tighter():
    html = render_tesla_cockpit_html(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.42,
                "battery_kw": 0.0,
                "grid_kw": 0.007,
            },
            "snapshot": {"battery_soc_percent": 67.0},
            "controller": {"setpoint_kw": 0.0},
            "valid_cycle": True,
        }
    )

    assert "V2352-R tighter powerflow card spacing" in html
    assert "height: 560px !important" in html
    assert "margin-top: -18px !important" in html
    assert "padding-bottom: 8px !important" in html
