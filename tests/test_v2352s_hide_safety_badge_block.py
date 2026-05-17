from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import render_tesla_cockpit_html


def test_v2352s_safety_rail_is_hidden_but_payload_remains_readonly():
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

    assert "V2352-S hide cockpit safety badge block" in html
    assert ".safety-rail" in html
    assert "display: none !important" in html
    assert '"read_only": true' in html
    assert '"observer_only": true' in html
    assert '"service_calls_allowed": false' in html
    assert '"write_controls_allowed": false' in html
