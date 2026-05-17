
from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_v2352j_nodes_are_circles_and_no_inner_value_capsules():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": -0.4,
                "grid_kw": 0.0,
                "load_kw": 0.4,
                "pv_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 69.0},
            "planner_timeline": [{"soc_percent": 68.2}],
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-node-circle" in html
    svg = html.split("<svg", 1)[1].split("</svg>", 1)[0]
    assert "<rect" not in svg
    assert 'data-node="battery" data-source="battery"' in html
    assert "pf-value-pill" not in html
    assert "ha-powerflow-large" in html


def test_v2352j_house_ring_can_show_mixed_sources():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": -0.5,
                "grid_kw": 0.0,
                "load_kw": 1.0,
                "pv_kw": 0.5,
            },
            "battery_soc_card": {"soc_percent": 80.0},
            "planner_timeline": [{"soc_percent": 78.8}],
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert 'data-node="house" data-source="solar"' in html
    assert 'data-node="house" data-source="battery"' in html


def test_v2352j_summary_cards_have_source_color_classes():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "battery_kw": 0.0,
                "grid_kw": 0.3,
                "load_kw": 0.3,
                "pv_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 55.0},
            "planner_timeline": [{"soc_percent": 54.3}],
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "pf-summary pf-summary-solar" in html
    assert "pf-summary pf-summary-home" in html
    assert "pf-summary pf-summary-battery" in html
    assert "pf-summary pf-summary-grid" in html
