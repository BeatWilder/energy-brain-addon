
from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
    render_tesla_cockpit_html,
)


def test_v2352m_uses_ha_like_card_style_and_no_cross_backbone():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.6,
                "load_kw": 1.1,
                "battery_kw": 0.5,
                "grid_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 95.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "ha-powerflow-card-style" in html
    assert "pf-cross" not in html
    assert 'viewBox="0 0 760 700"' in html
    assert "pf-junction-soft" in html


def test_v2352m_routes_are_curved_like_home_assistant_card():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.6,
                "load_kw": 1.1,
                "battery_kw": 0.5,
                "grid_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 95.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "M 380 180 C 395 245, 500 305, 560 315" in html
    assert "M 380 180 C 380 255, 380 355, 380 420" in html
    assert "M 200 315 C 295 315, 455 315, 560 315" in html


def test_v2352m_no_pv_keeps_solar_routes_idle_without_solar_animation():
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


def test_v2352m_rendered_full_html_contains_new_css():
    html = render_tesla_cockpit_html(
        {
            "snapshot": {
                "pv_power_kw": 0.6,
                "household_load_kw": 1.1,
                "battery_soc": 67.0,
            },
            "energy_flow": {
                "pv_kw": 0.6,
                "load_kw": 1.1,
                "battery_kw": 0.5,
                "grid_kw": 0.0,
            },
            "valid_cycle": True,
        }
    )

    assert "V2352-N bigger HA-like powerflow with passive lanes" in html
    assert "ha-powerflow-card-style" in html
