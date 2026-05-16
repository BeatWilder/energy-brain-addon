from __future__ import annotations

import json

from energy_brain.v2000.read_only_tesla_cockpit import (
    powerflow_edges,
    powerflow_explanation,
    powerflow_snapshot,
    render_powerflow_svg,
    render_tesla_cockpit_html,
)


def test_powerflow_snapshot_is_deterministic_and_rounded():
    payload = {"flow": {"pv_kw": 1.14, "load_kw": 0.94, "battery_setpoint_kw": 0.18, "grid_kw": -0.19, "battery_soc_percent": 81.6}}
    first = powerflow_snapshot(payload)
    second = powerflow_snapshot(payload)

    assert first == second
    assert first["pv_kw"] == 1.1
    assert first["load_kw"] == 0.9
    assert first["battery_kw"] == 0.2
    assert first["grid_kw"] == -0.2
    assert first["battery_soc_percent"] == 82
    assert first["read_only"] is True
    assert first["control_allowed"] is False


def test_powerflow_edges_show_understandable_directions():
    directions = {edge["direction"] for edge in powerflow_edges({"pv_kw": 1.2, "load_kw": 0.8, "battery_kw": 0.3, "grid_kw": -0.1})}
    assert "zon_naar_huis" in directions
    assert "zon_naar_batterij" in directions
    assert "net_export" in directions


def test_powerflow_edges_show_battery_and_grid_import():
    directions = {edge["direction"] for edge in powerflow_edges({"pv_kw": 0.1, "load_kw": 1.4, "battery_kw": -0.4, "grid_kw": 0.9})}
    assert "batterij_naar_huis" in directions
    assert "net_import" in directions


def test_missing_data_renders_safe_fallback():
    snapshot = powerflow_snapshot({})
    edges = powerflow_edges(snapshot)
    explanation = powerflow_explanation(snapshot, edges)

    assert snapshot["data_quality"] == "schaduwdata"
    assert edges[0]["active"] is False
    assert "niet genoeg duidelijke data" in explanation


def test_rendered_html_contains_powerflow_panel_and_svg_animation():
    html = render_tesla_cockpit_html({"flow": {"pv_kw": 1.2, "load_kw": 0.8, "battery_setpoint_kw": 0.3, "grid_kw": -0.1, "battery_soc_percent": 82}})

    assert "Energy Flow nu" in html
    assert "Stroomrichting" in html
    assert "Zon" in html
    assert "Huis" in html
    assert "Batterij" in html
    assert "Net" in html
    assert "Alleen meekijken" in html
    assert "Geen aansturing" in html
    assert "Dit is alleen een weergave. Energy Brain stuurt niets aan." in html
    assert "<svg" in html
    assert "animateMotion" in html
    assert "@keyframes eb-flow-dash" in html
    assert "prefers-reduced-motion" in html


def test_existing_plan_card_and_secondary_graph_still_render():
    html = render_tesla_cockpit_html({})
    assert "Planning in gewone taal" in html
    assert "Vandaag samengevat" in html
    assert "Technische grafiek voor controle" in html
    assert "Niet nodig voor dagelijks gebruik" in html


def test_powerflow_svg_is_read_only_display_only():
    snapshot = powerflow_snapshot({"flow": {"pv_kw": 1.0, "load_kw": 1.0}})
    svg = render_powerflow_svg(snapshot, powerflow_edges(snapshot))

    assert 'data-read-only="true"' in svg
    assert "Geen aansturing" in svg


def test_json_payload_remains_raw_parseable_json():
    html = render_tesla_cockpit_html({})
    start = html.index('<script id="cockpit-payload"')
    start = html.index(">", start) + 1
    end = html.index("</script>", start)
    raw = html[start:end]

    assert "&quot;" not in raw
    payload = json.loads(raw)
    assert payload["read_only"] is True
