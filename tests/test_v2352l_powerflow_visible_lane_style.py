from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
    render_tesla_cockpit_html,
)


def test_v2352l_rendered_html_contains_obvious_thin_lane_css():
    html = render_tesla_cockpit_html(
        {
            "snapshot": {
                "pv_power_kw": 0.0,
                "household_load_kw": 0.8,
                "battery_soc": 67.0,
            },
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.8,
                "battery_kw": 0.0,
                "grid_kw": 0.8,
            },
            "valid_cycle": True,
        }
    )

    assert "V2352-L obvious thin HA-style lanes" in html
    assert "stroke-width: 1.7 !important" in html
    assert "opacity: .10 !important" in html


def test_v2352l_no_pv_keeps_solar_route_idle_and_no_extra_solar_dot():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.8,
                "battery_kw": 0.0,
                "grid_kw": 0.8,
            },
            "battery_soc_card": {"soc_percent": 67.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-edge pf-edge-zon_naar_huis idle" in html
    assert "pf-edge pf-edge-zon_naar_batterij idle" in html
    assert "pf-edge pf-edge-net_import active" in html
    assert html.count('class="pf-dot"') == 1
    assert 'r="2.1"' in html
