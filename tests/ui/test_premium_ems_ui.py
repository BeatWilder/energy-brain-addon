from energy_brain.ui.layout_router import build_layout_view
from energy_brain.ui.renderer import render_layout


def test_power_values_are_sanitized_for_display():
    layout = build_layout_view(
        {
            "battery_soc_percent": 140,
            "pv_power_kw": -999,
            "household_load_kw": "unavailable",
            "battery_power_kw": 4.2,
            "grid_power_kw": -2.5,
        },
        "mobile",
    )

    hero = next(section for section in layout["sections"] if section["type"] == "powerflow_hero")

    assert hero["soc_label"] == "100%"
    assert hero["solar_label"] == "30.0 kW"
    assert hero["house_label"] == "unavailable"
    assert "solar" in hero["data_quality"]["clamped"]
    assert "home" in hero["data_quality"]["unknown"]


def test_rendered_ui_contains_health_strip_and_responsive_script():
    html = render_layout(
        "auto",
        {
            "battery_soc_percent": 72,
            "pv_power_kw": 2.4,
            "household_load_kw": 1.1,
            "battery_power_kw": 0.8,
            "grid_power_kw": -0.5,
        },
    )

    assert "health-strip" in html
    assert "data-layout-option=\"auto\"" in html
    assert "window.addEventListener(\"resize\"" in html
    assert "quality-live" in html


def test_import_export_state_is_visible():
    html = render_layout(
        "mobile",
        {
            "battery_soc_percent": 70,
            "pv_power_kw": 4.0,
            "household_load_kw": 1.0,
            "battery_power_kw": 0.5,
            "grid_power_kw": -1.2,
        },
    )

    assert 'data-grid-flow="exporting"' in html
    assert ">Export</span>" in html
