
from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_tesla_cockpit_html,
    render_powerflow_svg,
)


def _snapshot() -> dict:
    return powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.8,
                "load_kw": 1.2,
                "battery_kw": -0.4,
                "grid_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 79.0},
        }
    )


def test_powerflow_has_source_color_css_tokens():
    html = render_tesla_cockpit_html(
        {
            "snapshot": {
                "pv_power_kw": 0.8,
                "household_load_kw": 1.2,
                "battery_soc": 79.0,
            },
            "energy_flow": {
                "pv_kw": 0.8,
                "load_kw": 1.2,
                "battery_kw": -0.4,
                "grid_kw": 0.0,
            },
            "valid_cycle": True,
        }
    )

    assert "pf-ring-solar" in html
    assert "pf-ring-home" in html
    assert "pf-ring-battery" in html
    assert "pf-ring-grid" in html
    assert "pf-source-solar" in html
    assert "pf-source-battery" in html
    assert "pf-source-grid" in html


def test_powerflow_svg_values_have_no_inner_capsules():
    snapshot = _snapshot()
    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-value-pill" not in html
    assert "pf-sun-pill" not in html
    assert "pf-home-pill" not in html
    assert "pf-battery-pill" not in html
    assert "pf-grid-pill" not in html
    assert "79.0% nu" in html or "79% nu" in html


def test_powerflow_summary_cards_use_matching_source_classes():
    snapshot = _snapshot()
    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-summary pf-summary-solar" in html
    assert "pf-summary pf-summary-home" in html
    assert "pf-summary pf-summary-battery" in html
    assert "pf-summary pf-summary-grid" in html


def test_powerflow_edges_get_direction_classes_for_colored_routes():
    snapshot = _snapshot()
    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-edge pf-edge-batterij_naar_huis pf-source-battery active" in html
    assert "pf-edge pf-edge-zon_naar_huis pf-source-solar" in html
