from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .planner import Plan, STEP_HOURS, simulate_next_soc


@dataclass(frozen=True)
class ControllerDecision:
    approved: bool
    execute: bool
    action: str
    setpoint_kw: float
    reasons: list[str]


def validate_and_decide(plan: Plan, config: AppConfig) -> ControllerDecision:
    reasons = _validate_plan(plan, config)
    if reasons:
        return ControllerDecision(False, False, "no_action", 0.0, reasons)

    if config.mode in {"observer", "shadow"}:
        return ControllerDecision(True, False, plan.action, plan.steps[0].battery_setpoint_kw, [f"{config.mode}_mode_no_write"])

    if not config.command.configured:
        return ControllerDecision(False, False, "no_action", 0.0, ["missing_command_configuration"])

    return ControllerDecision(True, True, plan.action, plan.steps[0].battery_setpoint_kw, ["active_mode_controller_approved"])


def _validate_plan(plan: Plan, config: AppConfig) -> list[str]:
    errors: list[str] = []
    battery = config.battery
    if battery is None:
        return ["missing_or_invalid_battery_limits"]
    if not plan.valid:
        return list(plan.errors or ["invalid_plan"])
    if not plan.steps or len(plan.soc_trajectory) != len(plan.steps) + 1:
        errors.append("missing_soc_trajectory")
    for step in plan.steps:
        if abs(step.battery_setpoint_kw) > max(battery.max_charge_kw, battery.max_discharge_kw):
            errors.append(f"power_limit_violation_step_{step.index}")
        if step.battery_setpoint_kw > battery.max_charge_kw:
            errors.append(f"charge_limit_violation_step_{step.index}")
        if -step.battery_setpoint_kw > battery.max_discharge_kw:
            errors.append(f"discharge_limit_violation_step_{step.index}")
        if not battery.soc_min_percent <= step.soc_percent <= battery.soc_max_percent:
            errors.append(f"soc_limit_violation_step_{step.index}")

    if plan.steps and plan.soc_trajectory:
        previous_soc = plan.soc_trajectory[0]
        for step in plan.steps:
            expected_soc = simulate_next_soc(previous_soc, step.battery_setpoint_kw, battery)
            if abs(expected_soc - step.soc_percent) > 1e-4:
                errors.append(f"soc_physics_mismatch_step_{step.index}")
            previous_soc = step.soc_percent

    if STEP_HOURS != 0.25:
        errors.append("invalid_timestep")
    return errors
