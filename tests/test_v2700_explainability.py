from energy_brain.v2700.explainability import (
    build_planner_explainability,
)


def test_reserve_soc_constraint():
    summary = {
        "snapshot": {
            "battery_soc_percent": 21,
            "grid_price": 0.35,
            "pv_power_kw": 0.2,
            "household_load_kw": 4.5,
        },
        "plan": {
            "steps": [
                {
                    "battery_setpoint_kw": -3.5,
                    "reason": "reserve_clamped_discharge",
                }
            ]
        }
    }

    result = build_planner_explainability(summary)

    assert result["decision"] == "discharge"

    assert "high_import_price" in result["reasons"]

    assert "reserve_soc_floor" in result["constraints"]

    assert result["observer_only"] is True

    assert result["write_allowed"] is False


def test_charge_window():
    summary = {
        "snapshot": {
            "battery_soc_percent": 55,
            "grid_price": 0.01,
            "pv_power_kw": 5.2,
            "household_load_kw": 0.7,
        },
        "plan": {
            "steps": [
                {
                    "battery_setpoint_kw": 2.0,
                    "reason": "cheap_charge_window",
                }
            ]
        }
    }

    result = build_planner_explainability(summary)

    assert result["decision"] == "charge"

    assert "cheap_energy_window" in result["reasons"]

    assert "solar_surplus" in result["badges"]
