from energy_brain.config import BatteryConfig
from energy_brain.planner import EnergySnapshot, build_plan


def battery() -> BatteryConfig:
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


def test_pv_charge_is_clamped_to_soc_max():
    plan = build_plan(
        EnergySnapshot(
            battery_soc_percent=94.0,
            pv_power_kw=5.0,
            grid_price=0.13,
            household_load_kw=1.0,
        ),
        battery(),
        horizon_steps=4,
    )

    assert plan.valid is True
    assert max(plan.soc_trajectory) <= 95.0
    assert plan.steps[0].reason == "max_soc_clamped_charge"
    assert plan.steps[0].battery_setpoint_kw > 0.0
    assert plan.steps[0].soc_percent == 95.0
    assert all(step.soc_percent <= 95.0 for step in plan.steps)


def test_max_soc_hold_when_already_full():
    plan = build_plan(
        EnergySnapshot(
            battery_soc_percent=95.0,
            pv_power_kw=5.0,
            grid_price=0.13,
            household_load_kw=1.0,
        ),
        battery(),
        horizon_steps=4,
    )

    assert plan.valid is True
    assert all(step.battery_setpoint_kw == 0.0 for step in plan.steps)
    assert all(step.soc_percent == 95.0 for step in plan.steps)
    assert all(step.reason == "max_soc_hold" for step in plan.steps)
