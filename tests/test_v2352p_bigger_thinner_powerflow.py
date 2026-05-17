from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
    render_tesla_cockpit_html,
)


def test_v2352p_powerflow_is_larger_and_uses_bigger_viewbox():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.42,
                "battery_kw": 0.0,
                "grid_kw": 0.007,
            },
            "battery_soc_card": {"soc_percent": 67.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert 'viewBox="0 0 760 820"' in html
    assert 'cy="605"' in html
    assert 'cx="640" cy="385"' in html
    assert 'cx="120" cy="385"' in html


def test_v2352p_rings_are_bigger_but_css_makes_them_thinner():
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

    assert "V2352-P bigger powerflow with thinner rings" in html
    assert 'r="82"' in html
    assert "stroke-width: 5.8" in html
    assert "min-height: 860px" in html


def test_v2352p_passive_lanes_still_visible_but_only_active_routes_get_dots():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.42,
                "battery_kw": 0.0,
                "grid_kw": 0.007,
            },
            "battery_soc_card": {"soc_percent": 67.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-edge pf-edge-zon_naar_huis pf-source-solar idle" in html
    assert "pf-edge pf-edge-net_import pf-source-grid" in html
    assert html.count('class="pf-dot') <= 1
