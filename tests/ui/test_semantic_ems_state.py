from energy_brain.ui.live.live_payload_adapter import build_live_payload
from energy_brain.ui.renderer import render_layout
from energy_brain.ui.semantic_state import CANONICAL_ENTITIES


def test_semantic_state_uses_canonical_entities_without_demo_values():
    payload = build_live_payload(
        {
            "entity_states": {
                "sensor.alphaess_soc_battery": {"state": "62"},
                "sensor.alphaess_power_battery": {"state": "1200"},
                "sensor.alphaess_current_pv_production": {"state": "3400"},
                "sensor.alphaess_current_house_load": {"state": "1800"},
                "sensor.alphaess_power_grid": {"state": "-300"},
                "sensor.current_electricity_market_price": {"state": "0.18"},
                "sensor.energybrain_required_reserve_soc": {"state": "35"},
                "binary_sensor.keuken_bezet_stabiel": {"state": "on"},
                "binary_sensor.verwarming_mag_nu_op_energie": {"state": "on"},
                "input_boolean.alphaess_helper_dispatch": {"state": "off"},
            }
        }
    )

    semantic = payload["semantic_state"]

    assert payload["battery_soc_percent"] == "62"
    assert payload["battery_power_kw"] == 1.2
    assert payload["pv_power_kw"] == 3.4
    assert payload["household_load_kw"] == 1.8
    assert payload["grid_power_kw"] == -0.3
    assert semantic["solar_state"] == "Zonne-overschot"
    assert semantic["grid_dependency"] == "Teruglevering"
    assert semantic["comfort_mode"] == "Comfort bewaakt"
    assert semantic["dispatch_state"] == "Helper uit"
    assert payload["canonical_entities"]["battery_soc_percent"] == CANONICAL_ENTITIES["battery_soc_percent"]


def test_semantic_ui_sections_render_as_unknown_when_entities_are_missing():
    html = render_layout("desktop", build_live_payload({}))

    assert "Comfort Intelligence" in html
    assert "Living Controls" in html
    assert "Dispatch onbekend" in html
    assert "Comfort onbekend" in html or "Aanwezigheid onbekend" in html
    assert "30.0 kW" not in html
    assert "3.2 kW" not in html


def test_planner_hero_reacts_to_semantic_state():
    html = render_layout(
        "desktop",
        build_live_payload(
            {
                "entity_states": {
                    "sensor.alphaess_soc_battery": {"state": "18"},
                    "sensor.energybrain_required_reserve_soc": {"state": "25"},
                    "sensor.alphaess_power_battery": {"state": "0"},
                    "sensor.alphaess_power_grid": {"state": "900"},
                }
            }
        ),
    )

    assert "Reserve beschermen" in html
    assert "Hard floor actief" in html or "Reserve beschermd" in html
    assert 'data-energy-state="scarcity"' in html
