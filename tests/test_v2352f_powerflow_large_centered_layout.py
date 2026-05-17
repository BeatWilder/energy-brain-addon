
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

    assert 'viewBox="0 0 760 820"' in html
    assert "ha-powerflow-large" in html
    assert "ha-powerflow-card-style" in html
    assert "pf-node-circle" in html


def test_powerflow_paths_keep_ha_like_curved_routes_and_soft_junction():
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

    assert "pf-cross" not in html
    assert "pf-junction-soft" in html
    assert "M 380 170 C 405 265, 525 365, 625 385" in html
    assert "Batterij helpt het huis" in html


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
