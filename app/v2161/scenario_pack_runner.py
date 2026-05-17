"""Run deterministic offline planner quality scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2129.planner_replay_audit_report import build_planner_replay_audit_report
from app.v2160.planner_quality_scenarios import PlannerQualityScenario, get_planner_quality_scenarios


@dataclass(frozen=True)
class ScenarioResult:
    scenario_name: str
    valid: bool
    observer_only: bool
    execution_allowed: bool
    best_strategy_name: str | None
    summary_markdown: str
    total_strategy_count: int
    slot_line_count: int
    min_soc_kwh: float
    final_soc_kwh: float
    reason_codes: tuple[str, ...]
    expected_focus: str
    notes: str


@dataclass(frozen=True)
class ScenarioPackResult:
    valid: bool
    observer_only: bool
    execution_allowed: bool
    scenario_results: tuple[ScenarioResult, ...]
    passed_count: int
    failed_count: int
    reason_codes: tuple[str, ...]


def run_planner_quality_scenario_pack() -> ScenarioPackResult:
    """Run every offline quality scenario in deterministic order."""

    scenario_results = tuple(_run_scenario(scenario) for scenario in get_planner_quality_scenarios())
    passed_count = sum(1 for result in scenario_results if result.valid)
    failed_count = len(scenario_results) - passed_count

    return ScenarioPackResult(
        valid=failed_count == 0,
        observer_only=True,
        execution_allowed=False,
        scenario_results=scenario_results,
        passed_count=passed_count,
        failed_count=failed_count,
        reason_codes=("planner_quality_scenario_pack", "observer_only_no_execution"),
    )


def _run_scenario(scenario: PlannerQualityScenario) -> ScenarioResult:
    try:
        report = build_planner_replay_audit_report(scenario.fixture)
        loaded = build_simulation_input(scenario.fixture)
        validation_codes = _validation_reason_codes(scenario.fixture, report, loaded.valid)
        required_codes = _required_reason_codes(scenario, report.reason_codes)
        reason_codes = report.reason_codes + validation_codes + required_codes
        valid = (
            scenario.expected_safe
            and report.valid
            and report.observer_only
            and not report.execution_allowed
            and not validation_codes
            and not required_codes
        )
        winner = next((line for line in report.strategy_lines if line.is_winner), None)
        return ScenarioResult(
            scenario_name=scenario.scenario_name,
            valid=valid,
            observer_only=True,
            execution_allowed=False,
            best_strategy_name=report.best_strategy_name,
            summary_markdown=report.summary_markdown,
            total_strategy_count=len(report.strategy_lines),
            slot_line_count=len(report.slot_lines),
            min_soc_kwh=winner.min_soc_kwh if winner is not None else 0.0,
            final_soc_kwh=winner.final_soc_kwh if winner is not None else 0.0,
            reason_codes=reason_codes or ("scenario_validation_failed_explicitly",),
            expected_focus=scenario.expected_focus,
            notes=scenario.notes,
        )
    except (TypeError, ValueError, AttributeError, KeyError) as exc:
        return ScenarioResult(
            scenario_name=scenario.scenario_name,
            valid=False,
            observer_only=True,
            execution_allowed=False,
            best_strategy_name=None,
            summary_markdown="invalid scenario: no offline audit report was produced",
            total_strategy_count=0,
            slot_line_count=0,
            min_soc_kwh=0.0,
            final_soc_kwh=0.0,
            reason_codes=("scenario_exception_failed_safe", _clean_error(exc), "observer_only_no_execution"),
            expected_focus=scenario.expected_focus,
            notes=scenario.notes,
        )


def _validation_reason_codes(
    fixture: Mapping[str, Any],
    report: Any,
    loaded_valid: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not report.observer_only:
        reason_codes.append("scenario_report_not_observer_only")
    if report.execution_allowed:
        reason_codes.append("scenario_report_allowed_execution")
    if report.valid and not report.strategy_lines:
        reason_codes.append("valid_scenario_empty_strategy_lines")
    if report.valid and not report.slot_lines:
        reason_codes.append("valid_scenario_empty_slot_lines")
    if not report.valid:
        reason_codes.append("scenario_audit_report_invalid")
    if not loaded_valid:
        reason_codes.append("scenario_fixture_invalid")

    battery = fixture.get("battery", {}) if isinstance(fixture, Mapping) else {}
    if isinstance(battery, Mapping) and report.strategy_lines:
        winner = next((line for line in report.strategy_lines if line.is_winner), None)
        if winner is not None:
            min_floor = max(float(battery.get("min_soc_kwh", 0.0)), float(battery.get("reserve_kwh", 0.0)))
            max_soc = float(battery.get("max_soc_kwh", 0.0))
            if winner.min_soc_kwh < min_floor:
                reason_codes.append("scenario_min_soc_below_floor")
            if not min_floor <= winner.final_soc_kwh <= max_soc:
                reason_codes.append("scenario_final_soc_outside_bounds")

    return tuple(reason_codes)


def _required_reason_codes(
    scenario: PlannerQualityScenario,
    report_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    missing = [
        reason_code
        for reason_code in scenario.required_reason_codes
        if reason_code not in report_reason_codes
    ]
    return tuple(f"missing_required_reason_code:{reason_code}" for reason_code in missing)


def _clean_error(exc: BaseException) -> str:
    text = str(exc).strip("'")
    return text or exc.__class__.__name__


__all__ = [
    "ScenarioPackResult",
    "ScenarioResult",
    "run_planner_quality_scenario_pack",
]
