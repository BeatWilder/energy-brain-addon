"""Build explainable offline audit reports from controlled strategy replay."""

from __future__ import annotations

from typing import Any, Mapping

from app.v2000.predbat_lesson_simulation_contract import SimulationInput
from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2064.action_intent_contract import ActionIntent
from app.v2065.controlled_action_simulator import simulate_controlled_actions
from app.v2096.strategy_action_intent_builder import (
    build_baseline_action_intents,
    build_cheapest_window_charge_intents,
    build_export_aware_intents,
    build_hold_reserve_intents,
)
from app.v2097.controlled_strategy_replay import (
    ControlledStrategyReplayResult,
    ControlledStrategyResult,
    run_controlled_strategy_replay,
)
from app.v2128.planner_replay_audit_contract import (
    PlannerReplayAuditReport,
    SlotAuditLine,
    StrategyAuditLine,
)


def build_planner_replay_audit_report(
    fixture: Mapping[str, Any] | SimulationInput,
) -> PlannerReplayAuditReport:
    """Return a deterministic advisory audit report for controlled replay."""

    replay = run_controlled_strategy_replay(fixture)
    if not replay.valid:
        strategy_lines = tuple(_strategy_audit_line(replay, strategy) for strategy in replay.strategy_results)
        return PlannerReplayAuditReport(
            valid=False,
            observer_only=True,
            execution_allowed=False,
            best_strategy_name=replay.best_strategy_name,
            winning_reason_codes=(),
            losing_reason_codes=_losing_reason_codes(replay),
            strategy_lines=strategy_lines,
            slot_lines=(),
            summary_markdown=_summary_markdown(
                replay=replay,
                strategy_lines=strategy_lines,
                slot_lines=(),
                winning_reason_codes=(),
            ),
            reason_codes=replay.reason_codes + ("planner_replay_audit_invalid_replay",),
        )

    strategy_lines = tuple(_strategy_audit_line(replay, strategy) for strategy in replay.strategy_results)
    winning_reason_codes = _winning_reason_codes(replay)
    slot_lines = _slot_audit_lines(fixture)

    return PlannerReplayAuditReport(
        valid=True,
        observer_only=True,
        execution_allowed=False,
        best_strategy_name=replay.best_strategy_name,
        winning_reason_codes=winning_reason_codes,
        losing_reason_codes=_losing_reason_codes(replay),
        strategy_lines=strategy_lines,
        slot_lines=slot_lines,
        summary_markdown=_summary_markdown(
            replay=replay,
            strategy_lines=strategy_lines,
            slot_lines=slot_lines,
            winning_reason_codes=winning_reason_codes,
        ),
        reason_codes=replay.reason_codes + ("planner_replay_audit_report",),
    )


def _strategy_audit_line(
    replay: ControlledStrategyReplayResult,
    strategy: ControlledStrategyResult,
) -> StrategyAuditLine:
    is_winner = strategy.strategy_name == replay.best_strategy_name
    return StrategyAuditLine(
        strategy_name=strategy.strategy_name,
        is_winner=is_winner,
        valid=strategy.valid,
        observer_only=True,
        execution_allowed=False,
        total_cost=strategy.total_cost,
        total_grid_import_kwh=strategy.total_grid_import_kwh,
        total_grid_export_kwh=strategy.total_grid_export_kwh,
        final_soc_kwh=strategy.final_soc_kwh,
        min_soc_kwh=strategy.min_soc_kwh,
        max_soc_kwh=strategy.max_soc_kwh,
        action_intent_count=strategy.action_intent_count,
        action_types=strategy.action_types,
        reason_codes=strategy.reason_codes,
        audit_reason=_audit_reason(replay, strategy),
    )


def _audit_reason(
    replay: ControlledStrategyReplayResult,
    strategy: ControlledStrategyResult,
) -> str:
    if strategy.strategy_name == replay.best_strategy_name:
        return ",".join(_winning_reason_codes(replay))
    return ",".join(dict(_losing_reason_codes(replay)).get(strategy.strategy_name, ())) or "not_selected"


def _winning_reason_codes(replay: ControlledStrategyReplayResult) -> tuple[str, ...]:
    winner = _winner(replay)
    if winner is None:
        return ()

    reason_codes = ["lowest_total_cost"]
    if any(
        strategy.strategy_name != winner.strategy_name
        and strategy.valid
        and strategy.total_cost == winner.total_cost
        for strategy in replay.strategy_results
    ):
        reason_codes.append("deterministic_strategy_order_tie_break")
    return tuple(reason_codes)


def _losing_reason_codes(
    replay: ControlledStrategyReplayResult,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    winner = _winner(replay)
    losing: list[tuple[str, tuple[str, ...]]] = []

    for strategy in replay.strategy_results:
        if strategy.strategy_name == replay.best_strategy_name:
            continue
        if not strategy.valid:
            losing.append((strategy.strategy_name, ("invalid_strategy_result",)))
        elif winner is not None and strategy.total_cost == winner.total_cost:
            losing.append((strategy.strategy_name, ("tie_lost_by_strategy_order",)))
        elif winner is not None and strategy.total_cost > winner.total_cost:
            losing.append((strategy.strategy_name, ("higher_cost_than_winner",)))
        else:
            losing.append((strategy.strategy_name, ("not_selected_no_valid_winner",)))

    return tuple(losing)


def _winner(replay: ControlledStrategyReplayResult) -> ControlledStrategyResult | None:
    for strategy in replay.strategy_results:
        if strategy.strategy_name == replay.best_strategy_name:
            return strategy
    return None


def _slot_audit_lines(fixture: Mapping[str, Any] | SimulationInput) -> tuple[SlotAuditLine, ...]:
    loaded = build_simulation_input(fixture)
    if not loaded.valid or loaded.simulation_input is None:
        return ()

    simulation_input = loaded.simulation_input
    lines: list[SlotAuditLine] = []
    for strategy_name, action_intents in _strategy_action_intents(simulation_input):
        result = simulate_controlled_actions(simulation_input, action_intents)
        for trace in result.trace:
            lines.append(
                SlotAuditLine(
                    strategy_name=strategy_name,
                    slot_index=trace.slot_index,
                    action_type=trace.action_type_applied,
                    soc_start_kwh=trace.soc_start_kwh,
                    soc_end_kwh=trace.soc_end_kwh,
                    grid_import_kwh=trace.grid_import_kwh,
                    grid_export_kwh=trace.grid_export_kwh,
                    slot_cost=trace.slot_cost,
                    reason_codes=trace.reason_codes,
                )
            )

    return tuple(lines)


def _strategy_action_intents(
    simulation_input: SimulationInput,
) -> tuple[tuple[str, tuple[ActionIntent, ...]], ...]:
    return (
        ("baseline_self_consumption", build_baseline_action_intents(simulation_input)),
        ("cheapest_window_charge_controlled", build_cheapest_window_charge_intents(simulation_input, 1.0)),
        ("export_aware_controlled", build_export_aware_intents(simulation_input, 1.0)),
        ("hold_reserve_controlled", build_hold_reserve_intents(simulation_input)),
    )


def _summary_markdown(
    *,
    replay: ControlledStrategyReplayResult,
    strategy_lines: tuple[StrategyAuditLine, ...],
    slot_lines: tuple[SlotAuditLine, ...],
    winning_reason_codes: tuple[str, ...],
) -> str:
    winner = next((line for line in strategy_lines if line.is_winner), None)
    winner_name = winner.strategy_name if winner is not None else "None"
    winner_cost = _fmt(winner.total_cost) if winner is not None else "n/a"
    winner_final_soc = _fmt(winner.final_soc_kwh) if winner is not None else "n/a"
    winner_min_soc = _fmt(winner.min_soc_kwh) if winner is not None else "n/a"
    winner_reason = ", ".join(winning_reason_codes) if winning_reason_codes else "invalid replay"

    lines = [
        "# Planner Replay Audit",
        "",
        "## Safety",
        "- observer_only: true",
        "- execution_allowed: false",
        "- no dispatch",
        "",
        "## Winner",
        f"- strategy name: {winner_name}",
        f"- total cost: {winner_cost}",
        f"- final SOC: {winner_final_soc}",
        f"- min SOC: {winner_min_soc}",
        f"- reason: {winner_reason}",
    ]

    if not replay.valid:
        lines.append("- replay status: invalid replay; no strategy is selected")

    lines.extend(
        [
            "",
            "## Strategy comparison",
            "| strategy | winner | valid | cost | import | export | min_soc | final_soc | actions |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for line in strategy_lines:
        lines.append(
            "| "
            + " | ".join(
                [
                    line.strategy_name,
                    str(line.is_winner).lower(),
                    str(line.valid).lower(),
                    _fmt(line.total_cost),
                    _fmt(line.total_grid_import_kwh),
                    _fmt(line.total_grid_export_kwh),
                    _fmt(line.min_soc_kwh),
                    _fmt(line.final_soc_kwh),
                    _actions(line),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Slot trace summary",
            "| strategy | slot | action | soc_start | soc_end | import | export | cost | reasons |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if slot_lines:
        for line in slot_lines:
            lines.append(
                "| "
                + " | ".join(
                    [
                        line.strategy_name,
                        str(line.slot_index),
                        line.action_type,
                        _fmt(line.soc_start_kwh),
                        _fmt(line.soc_end_kwh),
                        _fmt(line.grid_import_kwh),
                        _fmt(line.grid_export_kwh),
                        _fmt(line.slot_cost),
                        ", ".join(line.reason_codes),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | invalid replay |")

    lines.extend(
        [
            "",
            "## Notes",
            "- offline only",
            "- candidate simulation only",
            "- no Home Assistant writes",
        ]
    )
    return "\n".join(lines)


def _actions(line: StrategyAuditLine) -> str:
    if line.action_intent_count == 0:
        return "0 none"
    return f"{line.action_intent_count} {','.join(line.action_types)}"


def _fmt(value: float) -> str:
    return f"{value:.6f}"


__all__ = ["build_planner_replay_audit_report"]
