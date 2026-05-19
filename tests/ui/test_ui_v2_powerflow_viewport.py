from energy_brain.ui.layout_router import build_layout_view
from energy_brain.ui.powerflow import build_powerflow_scene
from energy_brain.ui.renderer import render_layout
from energy_brain.ui.viewport import build_viewport_state, classify_viewport_width


def test_viewport_engine_is_canonical_and_mobile_first():
    assert classify_viewport_width(None) == "mobile"
    assert classify_viewport_width(430) == "mobile"
    assert classify_viewport_width(900) == "tablet"
    assert classify_viewport_width(1400) == "desktop"
    assert build_viewport_state("desktop").mode == "desktop"


def test_powerflow_scene_maps_reversals_to_physical_direction():
    scene = build_powerflow_scene(
        {
            "solar_kw": 0.75,
            "house_kw": 1.5,
            "battery_kw": -0.75,
            "grid_kw": -0.2,
            "soc_percent": 72,
        }
    )

    assert scene["battery_state"] == "discharging"
    assert scene["grid_state"] == "exporting"
    assert scene["nodes"]["home"]["ring"]
    assert any(item["source"] == "solar" for item in scene["house_mix"])
    assert any(item["source"] == "battery" for item in scene["house_mix"])


def test_flow_intensity_drives_animation_variables():
    low = build_powerflow_scene({"solar_kw": 0.2, "house_kw": 0.2, "battery_kw": 0, "grid_kw": 0})
    high = build_powerflow_scene({"solar_kw": 4.5, "house_kw": 4.5, "battery_kw": 0, "grid_kw": 0})

    low_lane = low["lanes"][0]["vars"]
    high_lane = high["lanes"][0]["vars"]

    assert float(high_lane["thickness"]) > float(low_lane["thickness"])
    assert float(high_lane["glow"]) > float(low_lane["glow"])
    assert int(high_lane["density"]) > int(low_lane["density"])
    assert float(high_lane["speed"].rstrip("s")) < float(low_lane["speed"].rstrip("s"))


def test_renderer_exposes_v2_runtime_and_reduced_motion_hooks():
    html = render_layout(
        "auto",
        {
            "battery_soc_percent": 72,
            "pv_power_kw": 4.5,
            "household_load_kw": 2.0,
            "battery_power_kw": -0.8,
            "grid_power_kw": -1.7,
        },
    )

    assert 'data-viewport="mobile"' in html
    assert "body[data-viewport=" in html
    assert "body.layout-mobile" not in html
    assert "--flow-intensity" in html
    assert "--particle-density" in html
    assert "prefers-reduced-motion" in html
    assert "Geavanceerde observerdiagnose" in html


def test_missing_telemetry_keeps_scene_readable_without_fake_particles():
    html = render_layout("mobile", {})

    assert "quality-degraded" in html
    assert "Meetdata mist" not in html
    assert ">onbekend<" not in html
    assert '<circle class="flow-dot' not in html
    assert "state-idle" in html


def test_planner_timeline_is_semantically_aggregated_without_planner_changes():
    windows = [
        {"start": f"{hour:02d}:00", "end": f"{hour + 1:02d}:00", "action": "hold", "reason": "reserve protected"}
        for hour in range(8, 13)
    ] + [
        {"start": f"{hour:02d}:00", "end": f"{hour + 1:02d}:00", "action": "charge", "reason": "solar surplus"}
        for hour in range(13, 17)
    ]

    layout = build_layout_view({"plan_windows": windows}, "mobile")
    planner = next(section for section in layout["sections"] if section["type"] == "planner_summary")

    assert planner["source_entry_count"] == 9
    assert len(planner["entries"]) == 2
    assert planner["entries"][0]["source_count"] == 5
    assert planner["entries"][1]["source_count"] == 4
