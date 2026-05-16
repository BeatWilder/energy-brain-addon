from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .config import BatteryConfig


STEP_HOURS = 0.25


@dataclass(frozen=True)
class EnergySnapshot:
    battery_soc_percent: float | None
    pv_power_kw: float | None
    grid_price: float | None
    household_load_kw: float | None


@dataclass(frozen=True)
class PlanStep:
    index: int
    battery_setpoint_kw: float
    soc_percent: float
    reason: str


@dataclass(frozen=True)
class Plan:
    valid: bool
    action: str
    expected_cost: float
    baseline_cost: float
    savings_vs_baseline: float
    soc_trajectory: list[float] = field(default_factory=list)
    steps: list[PlanStep] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def no_action(errors: Sequence[str]) -> Plan:
    return Plan(
        valid=False,
        action="no_action",
        expected_cost=0.0,
        baseline_cost=0.0,
        savings_vs_baseline=0.0,
        soc_trajectory=[],
        steps=[],
        errors=list(errors),
    )


def build_plan(snapshot: EnergySnapshot, battery: BatteryConfig | None, horizon_steps: int) -> Plan:
    errors = validate_inputs(snapshot, battery)
    if errors:
        return no_action(errors)

    assert battery is not None
    assert snapshot.battery_soc_percent is not None
    assert snapshot.grid_price is not None
    assert snapshot.pv_power_kw is not None
    assert snapshot.household_load_kw is not None

    soc = snapshot.battery_soc_percent
    steps: list[PlanStep] = []
    trajectory = [round(soc, 6)]
    expected_cost = 0.0
    baseline_cost = _baseline_cost(snapshot, horizon_steps)

    for index in range(horizon_steps):
        setpoint_kw, reason = _choose_setpoint(snapshot, battery, soc)
        next_soc = simulate_next_soc(soc, setpoint_kw, battery)
        reserve = max(battery.reserve_percent, battery.soc_min_percent)
        if not _within_bounds(next_soc, battery) or (setpoint_kw < 0 and next_soc < reserve):
            setpoint_kw = 0.0
            reason = "bounded_no_action"
            next_soc = soc

        net_grid_kw = snapshot.household_load_kw - snapshot.pv_power_kw + setpoint_kw
        grid_import_kw = max(0.0, net_grid_kw)
        grid_export_kw = max(0.0, -net_grid_kw)
        expected_cost += (grid_import_kw - grid_export_kw) * STEP_HOURS * snapshot.grid_price

        steps.append(
            PlanStep(
                index=index,
                battery_setpoint_kw=round(setpoint_kw, 6),
                soc_percent=round(next_soc, 6),
                reason=reason,
            )
        )
        soc = next_soc
        trajectory.append(round(soc, 6))

    return Plan(
        valid=True,
        action="set_battery_power",
        expected_cost=round(expected_cost, 6),
        baseline_cost=round(baseline_cost, 6),
        savings_vs_baseline=round(baseline_cost - expected_cost, 6),
        soc_trajectory=trajectory,
        steps=steps,
        errors=[],
    )


def validate_inputs(snapshot: EnergySnapshot, battery: BatteryConfig | None) -> list[str]:
    errors: list[str] = []
    if battery is None:
        errors.append("missing_or_invalid_battery_limits")
    for field_name, value in (
        ("battery_soc_percent", snapshot.battery_soc_percent),
        ("pv_power_kw", snapshot.pv_power_kw),
        ("grid_price", snapshot.grid_price),
        ("household_load_kw", snapshot.household_load_kw),
    ):
        if value is None:
            errors.append(f"missing_{field_name}")
    if snapshot.pv_power_kw is not None and snapshot.pv_power_kw < 0:
        errors.append("invalid_negative_pv_power_kw")
    if snapshot.household_load_kw is not None and snapshot.household_load_kw < 0:
        errors.append("invalid_negative_household_load_kw")
    if errors or battery is None or snapshot.battery_soc_percent is None:
        return errors
    if not _within_bounds(snapshot.battery_soc_percent, battery):
        errors.append("initial_soc_out_of_bounds")
    return errors


def simulate_next_soc(soc_percent: float, setpoint_kw: float, battery: BatteryConfig) -> float:
    energy_delta_kwh = setpoint_kw * STEP_HOURS
    if energy_delta_kwh >= 0:
        stored_kwh = energy_delta_kwh * battery.charge_efficiency
    else:
        stored_kwh = energy_delta_kwh / battery.discharge_efficiency
    return soc_percent + (stored_kwh / battery.capacity_kwh) * 100.0


def _baseline_cost(snapshot: EnergySnapshot, horizon_steps: int) -> float:
    assert snapshot.grid_price is not None
    assert snapshot.pv_power_kw is not None
    assert snapshot.household_load_kw is not None
    net_grid_kw = snapshot.household_load_kw - snapshot.pv_power_kw
    return net_grid_kw * STEP_HOURS * snapshot.grid_price * horizon_steps


def _choose_setpoint(snapshot: EnergySnapshot, battery: BatteryConfig, soc_percent: float) -> tuple[float, str]:
    reserve = max(battery.reserve_percent, battery.soc_min_percent)
    pv_surplus_kw = max(0.0, snapshot.pv_power_kw - snapshot.household_load_kw)  # type: ignore[operator]
    if pv_surplus_kw > 0 and soc_percent < battery.soc_max_percent:
        return min(pv_surplus_kw, battery.max_charge_kw), "charge_from_pv_surplus"
    if snapshot.grid_price < 0 and soc_percent < battery.soc_max_percent:  # type: ignore[operator]
        return battery.max_charge_kw, "charge_on_negative_price"
    if snapshot.grid_price > 0 and soc_percent > reserve and snapshot.household_load_kw > snapshot.pv_power_kw:  # type: ignore[operator]
        load_deficit_kw = snapshot.household_load_kw - snapshot.pv_power_kw
        available_percent = max(0.0, soc_percent - reserve)
        available_kwh = (available_percent / 100.0) * battery.capacity_kwh
        max_discharge_to_reserve_kw = (available_kwh * battery.discharge_efficiency) / STEP_HOURS

        requested_discharge_kw = min(
            load_deficit_kw,
            battery.max_discharge_kw,
        )
        allowed_discharge_kw = min(
            requested_discharge_kw,
            max_discharge_to_reserve_kw,
        )

        if allowed_discharge_kw <= 0:
            return 0.0, "reserve_hold"

        reason = (
            "reserve_clamped_discharge"
            if allowed_discharge_kw < requested_discharge_kw
            else "discharge_to_load"
        )
        return -allowed_discharge_kw, reason

    return 0.0, "hold"


def _within_bounds(soc_percent: float, battery: BatteryConfig) -> bool:
    return battery.soc_min_percent <= soc_percent <= battery.soc_max_percent
