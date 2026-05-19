from energy_brain.ui.live.live_payload_adapter import (
    build_live_payload,
)


def test_schema():
    payload = build_live_payload()

    assert payload["schema_version"] == \
        "phase_ui_i.live_payload.v1"


def test_observer_only():
    payload = build_live_payload()

    assert payload["observer_only"] is True


def test_no_dispatch():
    payload = build_live_payload()

    assert payload["dispatch_allowed"] is False
    assert payload["ha_writes_allowed"] is False
    assert payload["service_calls_allowed"] is False


def test_override():
    payload = build_live_payload({
        "soc_percent": 42,
    })

    assert payload["soc_percent"] == 42


def test_empty_payload_does_not_inject_demo_values():
    payload = build_live_payload()

    assert payload["soc_percent"] is None
    assert payload["pv_power_kw"] is None
    assert payload["grid_power_kw"] is None
    assert payload["battery_power_kw"] is None
    assert payload["degraded"] is True
    assert "Meetdata ontbreekt" in payload["degraded_text"]


def test_summary_snapshot_maps_to_live_display_payload():
    payload = build_live_payload(
        {
            "mode": "observer",
            "last_update": "2026-05-19T12:00:00+02:00",
            "snapshot": {
                "battery_soc_percent": 43,
                "pv_power_kw": 3.2,
                "household_load_kw": 1.4,
                "grid_power_kw": -0.7,
                "battery_power_kw": 1.1,
                "grid_price": 0.21,
            },
            "plan": {
                "delta_vs_baseline": 0.42,
                "steps": [
                    {
                        "index": 0,
                        "battery_setpoint_kw": 1.2,
                        "soc_percent": 44,
                        "reason": "charge_from_pv_surplus",
                    }
                ],
            },
        }
    )

    assert payload["battery_soc_percent"] == 43
    assert payload["pv_power_kw"] == 3.2
    assert payload["household_load_kw"] == 1.4
    assert payload["grid_power_kw"] == -0.7
    assert payload["battery_power_kw"] == 1.1
    assert payload["grid_price"] == 0.21
    assert payload["expected_savings"] == 0.42
    assert payload["timeline"][0]["action"] == "Laden gepland"
