from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
)


def test_powerflow_uses_large_centered_ha_style_viewbox_and_nodes():
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

    # Layout: sun top center, grid left, home right, battery bottom center.
    assert '<circle cx="380" cy="92" r="74"/>' in html
    assert '<rect x="80" y="225" width="150" height="110" rx="30"/>' in html
    assert '<rect x="530" y="225" width="150" height="110" rx="30"/>' in html
    assert '<rect x="295" y="388" width="170" height="112" rx="32"/>' in html
    assert '<circle class="pf-junction" cx="380" cy="280" r="7" />' in html


def test_powerflow_paths_use_single_center_junction_shape():
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

    assert "M 380 168 L 380 392" in html
    assert "M 230 280 L 530 280" in html
    assert "M 380 388 C 380 330, 455 280, 530 280" in html
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
