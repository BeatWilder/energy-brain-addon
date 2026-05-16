from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_snapshot,
    render_powerflow_svg,
    render_tesla_cockpit_html,
)


PAYLOAD = {
    "energy_flow": {
        "battery_kw": 2.645,
        "grid_kw": -2.65,
        "load_kw": 0.738,
        "pv_kw": 3.383,
    },
    "battery_soc_card": {
        "soc_percent": 87.2,
    },
}


def test_powerflow_reads_current_api_energy_flow_shape():
    snapshot = powerflow_snapshot(PAYLOAD)

    assert snapshot["pv_kw"] == 3.4
    assert snapshot["load_kw"] == 0.7
    assert snapshot["battery_kw"] == 2.6
    assert snapshot["grid_kw"] == -2.6
    assert snapshot["battery_soc_percent"] == 87
    assert snapshot["data_quality"] == "live/schaduwdata"
    assert snapshot["read_only"] is True
    assert snapshot["control_allowed"] is False


def test_powerflow_edges_from_current_api_shape_show_solar_battery_and_export():
    snapshot = powerflow_snapshot(PAYLOAD)
    edges = powerflow_edges(snapshot)
    directions = {edge["direction"] for edge in edges}

    assert "zon_naar_huis" in directions
    assert "zon_naar_batterij" in directions
    assert "net_export" in directions


def test_direct_powerflow_svg_uses_current_api_values_and_labels():
    snapshot = powerflow_snapshot(PAYLOAD)
    html = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert "Energy Flow nu" in html
    assert "Stroomrichting - live/schaduwdata" in html
    assert "3.4 kW" in html
    assert "0.7 kW" in html
    assert "2.6 kW" in html
    assert "87%" in html
    assert "Overschot naar batterij" in html
    assert "Export naar net" in html
    assert "beperkte data" not in html
    assert 'data-read-only="true"' in html


def test_full_cockpit_still_contains_powerflow_section():
    html = render_tesla_cockpit_html(PAYLOAD)

    assert "Energy Flow nu" in html
    assert "Stroomrichting" in html
    assert "Zon" in html
    assert "Huis" in html
    assert "Batterij" in html
    assert "Net" in html
    assert "Dit is alleen een weergave. Energy Brain stuurt niets aan." in html
