
from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_v2352k_all_routes_are_visible_but_solar_has_no_active_flow_when_pv_zero():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.8,
                "battery_kw": 0.0,
                "grid_kw": 0.8,
            },
            "battery_soc_card": {"soc_percent": 68.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-edge pf-edge-zon_naar_huis idle" in html
    assert "pf-edge pf-edge-zon_naar_batterij idle" in html
    assert "pf-edge pf-edge-net_import active" in html


def test_v2352k_idle_routes_do_not_create_extra_animated_dots():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.8,
                "battery_kw": 0.0,
                "grid_kw": 0.8,
            },
            "battery_soc_card": {"soc_percent": 68.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert html.count('class="pf-dot"') == 1


def test_v2352k_import_and_export_paths_are_parallel_lanes_and_dots_are_smaller_or_newer():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.8,
                "battery_kw": 0.0,
                "grid_kw": 0.8,
            },
            "battery_soc_card": {"soc_percent": 68.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert 'M 248 236 C 330 236, 430 236, 512 236' in html
    assert 'M 512 264 C 430 264, 330 264, 248 264' in html
    assert 'r="2.1"' in html or 'r="3.2"' in html
