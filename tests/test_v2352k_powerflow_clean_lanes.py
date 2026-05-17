
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

    assert "pf-edge pf-edge-zon_naar_huis pf-source-solar idle" in html
    assert "pf-edge pf-edge-zon_naar_batterij pf-source-solar idle" in html
    assert "pf-edge pf-edge-net_import pf-source-grid active" in html


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

    assert html.count('class="pf-dot') == 1


def test_v2352k_import_and_export_paths_are_parallel_lanes_or_ha_like_routes():
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

    assert "M 242 286 C 314 286, 442 286, 518 286" in html
    assert "M 380 180 C 350 230, 300 286, 242 286" in html
    assert 'class="pf-dot' in html
