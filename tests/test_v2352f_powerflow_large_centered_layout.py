
from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_powerflow_uses_large_centered_ha_style_viewbox_and_circular_nodes():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.6,
                "load_kw": 1.1,
                "battery_kw": -0.5,
                "grid_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 95.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert 'viewBox="0 0 760 560"' in html
    assert "ha-powerflow-large" in html
    assert "powerflow-svg compact ha-flow" in html
    assert "pf-node-circle" in html
    assert 'data-node="solar"' in html
    assert 'data-node="grid"' in html
    assert 'data-node="house"' in html
    assert 'data-node="battery"' in html


def test_powerflow_paths_keep_single_center_junction_shape():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.5,
                "battery_kw": -0.5,
                "grid_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 80.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert '<line x1="380" y1="176" x2="380" y2="390">' in html
    assert '<line x1="180" y1="250" x2="580" y2="250">' in html
    assert "Batterij helpt het huis" in html
    assert "Net bijna nul" in html


def test_powerflow_keeps_existing_plain_text_and_readonly_safety():
    snapshot = powerflow_snapshot(
        {
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.5,
                "battery_kw": -0.5,
                "grid_kw": 0.0,
            },
            "battery_soc_card": {"soc_percent": 80.0},
        }
    )

    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert 'data-read-only="true"' in html
    assert "Dit is alleen een weergave. Energy Brain stuurt niets aan." in html
    assert "Energy Flow nu" in html
    assert "Waar komt de stroom nu vandaan" in html
    assert "powerflow-summary-grid" in html
