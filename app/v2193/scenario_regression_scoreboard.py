"""Build a deterministic offline scoreboard over planner quality scenarios."""

from __future__ import annotations

from app.v2129.planner_replay_audit_report import build_planner_replay_audit_report
from app.v2160.planner_quality_scenarios import get_planner_quality_scenarios
from app.v2161.scenario_pack_runner import ScenarioResult, run_planner_quality_scenario_pack
from app.v2192.scenario_regression_scoreboard_contract import (
    ScenarioRegressionScoreboard,
    ScenarioScoreboardRow,
)


def build_scenario_regression_scoreboard() -> ScenarioRegressionScoreboard:
    """Summarize deterministic planner quality scenario results."""

    pack_result = run_planner_quality_scenario_pack()
    fixtures_by_name = {
        scenario.scenario_name: scenario.fixture
        for scenario in get_planner_quality_scenarios()
    }
    rows = tuple(
        _scoreboard_row(
            scenario_result,
            fixtures_by_name.get(scenario_result.scenario_name),
        )
        for scenario_result in pack_result.scenario_results
    )
    passed_count = sum(1 for row in rows if row.safety_passed)
    failed_count = len(rows) - passed_count

    return ScenarioRegressionScoreboard(
        valid=failed_count == 0,
        observer_only=True,
        execution_allowed=False,
        rows=rows,
        passed_count=passed_count,
        failed_count=failed_count,
        summary_markdown=_summary_markdown(rows, passed_count, failed_count),
        reason_codes=pack_result.reason_codes + ("scenario_regression_scoreboard",),
    )


def _scoreboard_row(
    scenario_result: ScenarioResult,
    fixture: object,
) -> ScenarioScoreboardRow:
    total_cost, total_import, total_export = _winner_totals(fixture)
    failure_reason_codes = _regression_failure_reason_codes(scenario_result)
    regression_reason_codes = failure_reason_codes or ("regression_passed",)
    safety_passed = len(failure_reason_codes) == 0

    return ScenarioScoreboardRow(
        scenario_name=scenario_result.scenario_name,
        expected_focus=scenario_result.expected_focus,
        best_strategy_name=scenario_result.best_strategy_name,
        valid=scenario_result.valid,
        observer_only=True,
        execution_allowed=False,
        total_cost=total_cost,
        total_grid_import_kwh=total_import,
        total_grid_export_kwh=total_export,
        min_soc_kwh=scenario_result.min_soc_kwh,
        final_soc_kwh=scenario_result.final_soc_kwh,
        strategy_count=scenario_result.total_strategy_count,
        slot_line_count=scenario_result.slot_line_count,
        safety_passed=safety_passed,
        regression_reason_codes=regression_reason_codes,
        notes=scenario_result.notes,
    )


def _winner_totals(fixture: object) -> tuple[float, float, float]:
    if fixture is None:
        return (0.0, 0.0, 0.0)
    report = build_planner_replay_audit_report(fixture)
    winner = next((line for line in report.strategy_lines if line.is_winner), None)
    if winner is None:
        return (0.0, 0.0, 0.0)
    return (
        winner.total_cost,
        winner.total_grid_import_kwh,
        winner.total_grid_export_kwh,
    )


def _regression_failure_reason_codes(scenario_result: ScenarioResult) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not scenario_result.valid:
        reason_codes.append("scenario_result_invalid")
    if not scenario_result.observer_only:
        reason_codes.append("observer_only_required")
    if scenario_result.execution_allowed:
        reason_codes.append("execution_not_allowed")
    if scenario_result.total_strategy_count <= 0:
        reason_codes.append("strategy_count_required")
    if scenario_result.slot_line_count <= 0:
        reason_codes.append("slot_line_count_required")
    if scenario_result.final_soc_kwh is None:
        reason_codes.append("final_soc_required")
    if scenario_result.min_soc_kwh is None:
        reason_codes.append("min_soc_required")
    return tuple(reason_codes)


def _summary_markdown(
    rows: tuple[ScenarioScoreboardRow, ...],
    passed_count: int,
    failed_count: int,
) -> str:
    lines = [
        "# Scenario Regression Scoreboard",
        "",
        "## Safety",
        "- observer_only: true",
        "- execution_allowed: false",
        "- offline only",
        "",
        "## Summary",
        f"- passed count: {passed_count}",
        f"- failed count: {failed_count}",
        "",
        "## Rows",
        "| scenario | focus | best_strategy | valid | safety | cost | import | export | min_soc | final_soc | strategies | slots |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.scenario_name,
                    _table_text(row.expected_focus),
                    row.best_strategy_name or "None",
                    str(row.valid).lower(),
                    str(row.safety_passed).lower(),
                    _fmt(row.total_cost),
                    _fmt(row.total_grid_import_kwh),
                    _fmt(row.total_grid_export_kwh),
                    _fmt(row.min_soc_kwh),
                    _fmt(row.final_soc_kwh),
                    str(row.strategy_count),
                    str(row.slot_line_count),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "- candidate simulation only",
            "- no dispatch",
            "- no Home Assistant writes",
        ]
    )
    return "\n".join(lines)


def _table_text(value: str) -> str:
    return value.replace("|", "/")


def _fmt(value: float) -> str:
    return f"{value:.6f}"


__all__ = ["build_scenario_regression_scoreboard"]
