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


def test_final_discharge_step_is_labeled_as_reserve_clamped():
    plan = build_plan(
        EnergySnapshot(
            battery_soc_percent=21.0,
            pv_power_kw=0.0,
            grid_price=0.30,
            household_load_kw=5.0,
        ),
        battery(),
        horizon_steps=96,
    )

    assert plan.valid is True
    assert min(plan.soc_trajectory) == 20.0

    clamped_steps = [
        step for step in plan.steps
        if step.reason == "reserve_clamped_discharge"
    ]

    assert len(clamped_steps) == 1
    assert clamped_steps[0].soc_percent == 20.0
    assert clamped_steps[0].battery_setpoint_kw < 0.0

    after_clamp = plan.steps[clamped_steps[0].index + 1:]
    assert after_clamp
    assert all(step.battery_setpoint_kw == 0.0 for step in after_clamp)
    assert all(step.soc_percent == 20.0 for step in after_clamp)


def test_reserve_hold_when_no_energy_above_reserve():
    plan = build_plan(
        EnergySnapshot(
            battery_soc_percent=20.0,
            pv_power_kw=0.0,
            grid_price=0.30,
            household_load_kw=1.0,
        ),
        battery(),
        horizon_steps=4,
    )

    assert plan.valid is True
    assert all(step.battery_setpoint_kw == 0.0 for step in plan.steps)
    assert all(step.soc_percent == 20.0 for step in plan.steps)
    assert all(step.reason == "reserve_hold" for step in plan.steps)
