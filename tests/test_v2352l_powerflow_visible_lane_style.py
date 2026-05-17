
from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
    render_tesla_cockpit_html,
)


def test_v2352l_rendered_html_contains_obvious_thin_lane_css_or_newer():
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

    assert "V2352-L obvious thin HA-style lanes" in html or "V2352-M HA-like read-only powerflow card render" in html
    assert "stroke-width:" in html
    assert "opacity:" in html


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

    assert "pf-edge pf-edge-zon_naar_huis pf-source-solar idle" in html
    assert "pf-edge pf-edge-zon_naar_batterij pf-source-solar idle" in html
    assert "pf-edge pf-edge-net_import pf-source-grid active" in html
    assert html.count('class="pf-dot') == 1
