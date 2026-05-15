from energy_brain.config import BatteryConfig
from energy_brain.planner import EnergySnapshot, build_plan


def test_discharge_is_clamped_to_reserve_not_rejected_afterwards():
    battery = BatteryConfig(
        capacity_kwh=9.5,
        soc_min_percent=10.0,
        soc_max_percent=95.0,
        reserve_percent=20.0,
        max_charge_kw=5.0,
        max_discharge_kw=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    snapshot = EnergySnapshot(
        battery_soc_percent=21.0,
        pv_power_kw=0.0,
        grid_price=0.30,
        household_load_kw=3.0,
    )

    plan = build_plan(snapshot, battery, 4)

    assert plan.valid
    assert min(plan.soc_trajectory) >= 20.0
    assert plan.steps[0].battery_setpoint_kw < 0.0
    assert plan.steps[0].soc_percent >= 20.0
    assert plan.steps[1].battery_setpoint_kw == 0.0
    assert plan.steps[1].reason in {"reserve_hold", "hold"}


def test_reserve_hold_when_already_at_reserve():
    battery = BatteryConfig(
        capacity_kwh=9.5,
        soc_min_percent=10.0,
        soc_max_percent=95.0,
        reserve_percent=20.0,
        max_charge_kw=5.0,
        max_discharge_kw=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    snapshot = EnergySnapshot(
        battery_soc_percent=20.0,
        pv_power_kw=0.0,
        grid_price=0.30,
        household_load_kw=3.0,
    )

    plan = build_plan(snapshot, battery, 4)

    assert plan.valid
    assert all(step.battery_setpoint_kw == 0.0 for step in plan.steps)
    assert all(soc == 20.0 for soc in plan.soc_trajectory)
