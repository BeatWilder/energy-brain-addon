from energy_brain.config import BatteryConfig
from energy_brain.planner import EnergySnapshot, build_plan


def battery():
    return BatteryConfig(
        capacity_kwh=10.0,
        soc_min_percent=10.0,
        soc_max_percent=95.0,
        reserve_percent=20.0,
        max_charge_kw=5.0,
        max_discharge_kw=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )


def test_negative_pv_is_invalid_no_action():
    plan = build_plan(
        EnergySnapshot(
            battery_soc_percent=64.0,
            pv_power_kw=-8.0,
            grid_price=0.30,
            household_load_kw=1.1,
        ),
        battery(),
        96,
    )
    assert not plan.valid
    assert plan.action == "no_action"
    assert "invalid_negative_pv_power_kw" in plan.errors


def test_discharge_does_not_cross_reserve():
    plan = build_plan(
        EnergySnapshot(
            battery_soc_percent=21.0,
            pv_power_kw=0.0,
            grid_price=0.30,
            household_load_kw=5.0,
        ),
        battery(),
        96,
    )
    assert plan.valid
    assert min(plan.soc_trajectory) >= 20.0
