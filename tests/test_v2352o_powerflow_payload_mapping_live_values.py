from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import build_read_only_cockpit_payload


def test_v2352o_supplied_energy_flow_wins_over_snapshot_fallbacks():
    payload = build_read_only_cockpit_payload(
        {
            "snapshot": {
                "pv_power_kw": 8.0,
                "household_load_kw": 0.5,
                "battery_soc_percent": 67.0,
            },
            "energy_flow": {
                "pv_kw": 0.0,
                "load_kw": 0.42,
                "battery_kw": 0.0,
                "grid_kw": 0.007,
            },
            "controller": {"setpoint_kw": 0.0},
            "valid_cycle": True,
        }
    )

    assert payload["energy_flow"]["pv_kw"] == 0.0
    assert payload["energy_flow"]["load_kw"] == 0.42
    assert payload["energy_flow"]["grid_kw"] == 0.007


def test_v2352o_missing_powerflow_values_fallback_to_zero_not_demo_forecast():
    payload = build_read_only_cockpit_payload(
        {
            "snapshot": {
                "battery_soc_percent": 67.0,
            },
            "controller": {"setpoint_kw": 0.0},
            "valid_cycle": True,
        }
    )

    assert payload["energy_flow"]["pv_kw"] == 0.0
    assert payload["energy_flow"]["load_kw"] == 0.0
    assert payload["energy_flow"]["grid_kw"] == 0.0


def test_v2352o_snapshot_live_keys_are_used_when_no_energy_flow_supplied():
    payload = build_read_only_cockpit_payload(
        {
            "snapshot": {
                "pv_power_kw": 0.0,
                "household_load_kw": 0.42,
                "grid_power_kw": 0.007,
                "battery_soc_percent": 67.0,
            },
            "controller": {"setpoint_kw": 0.0},
            "valid_cycle": True,
        }
    )

    assert payload["energy_flow"]["pv_kw"] == 0.0
    assert payload["energy_flow"]["load_kw"] == 0.42
    assert payload["energy_flow"]["grid_kw"] == 0.007
