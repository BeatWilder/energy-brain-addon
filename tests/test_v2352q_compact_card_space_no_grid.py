from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import render_tesla_cockpit_html


def test_v2352q_powerflow_card_has_compact_spacing_and_no_grid_background():
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

    assert "V2352-Q compact powerflow card spacing and no grid lines" in html
    assert "height: 640px !important" in html
    assert "linear-gradient(90deg" in html  # page grid may still exist globally
    assert "background-size: auto !important" in html
    assert "margin-bottom: 8px !important" in html
