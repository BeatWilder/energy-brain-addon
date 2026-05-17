"""Replay offline strategies through the controlled action-intent simulator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from app.v2000.predbat_lesson_simulation_contract import SimulationInput
from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2064.action_intent_contract import ActionIntent
from app.v2065.controlled_action_simulator import ControlledActionResult, simulate_controlled_actions
from app.v2096.strategy_action_intent_builder import (
    build_baseline_action_intents,
    build_cheapest_window_charge_intents,
    build_export_aware_intents,
    build_hold_reserve_intents,
)


@dataclass(frozen=True)
class ControlledStrategyResult:
    strategy_name: str
    valid: bool
    observer_only: bool
    execution_allowed: bool
    total_cost: float
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    final_soc_kwh: float
    min_soc_kwh: float
    max_soc_kwh: float
    action_intent_count: int
    action_types: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ControlledStrategyReplayResult:
    valid: bool
    observer_only: bool
    execution_allowed: bool
    strategy_results: tuple[ControlledStrategyResult, ...]
    best_strategy_name: str | None
    reason_codes: tuple[str, ...]


StrategyBuilder = Callable[[SimulationInput], tuple[ActionIntent, ...]]


STRATEGY_ORDER: tuple[tuple[str, StrategyBuilder], ...] = (
    ("baseline_self_consumption", build_baseline_action_intents),
    (
        "cheapest_window_charge_controlled",
        lambda simulation_input: build_cheapest_window_charge_intents(simulation_input, 1.0),
    ),
    (
        "export_aware_controlled",
        lambda simulation_input: build_export_aware_intents(simulation_input, 1.0),
    ),
    ("hold_reserve_controlled", build_hold_reserve_intents),
)


def run_controlled_strategy_replay(
    fixture: Mapping[str, Any] | SimulationInput,
) -> ControlledStrategyReplayResult:
    """Build strategy intents and evaluate them through V2065."""

    loaded = build_simulation_input(fixture)
    if not loaded.valid or loaded.simulation_input is None:
        reason_codes = loaded.reason_codes + loaded.errors
        return ControlledStrategyReplayResult(
            valid=False,
            observer_only=True,
            execution_allowed=False,
            strategy_results=tuple(_invalid_strategy_result(name, reason_codes) for name, _ in STRATEGY_ORDER),
            best_strategy_name=None,
            reason_codes=reason_codes,
        )

    simulation_input = loaded.simulation_input
    strategy_results = tuple(
        _run_strategy(name, builder, simulation_input)
        for name, builder in STRATEGY_ORDER
    )
    valid_results = [result for result in strategy_results if result.valid]
    best_strategy_name = min(valid_results, key=lambda result: result.total_cost).strategy_name if valid_results else None

    return ControlledStrategyReplayResult(
        valid=all(result.valid for result in strategy_results),
        observer_only=True,
        execution_allowed=False,
        strategy_results=strategy_results,
        best_strategy_name=best_strategy_name,
        reason_codes=("controlled_strategy_replay", "observer_only_no_execution"),
    )


def _run_strategy(
    strategy_name: str,
    builder: StrategyBuilder,
    simulation_input: SimulationInput,
) -> ControlledStrategyResult:
    try:
        action_intents = tuple(builder(simulation_input))
    except (TypeError, ValueError, AttributeError) as exc:
        return _invalid_strategy_result(
            strategy_name,
            ("action_intent_generation_failed", _clean_error(exc), "observer_only_no_execution"),
        )

    result = simulate_controlled_actions(simulation_input, action_intents)
    return _strategy_result_from_controlled(strategy_name, result, action_intents)


def _strategy_result_from_controlled(
    strategy_name: str,
    result: ControlledActionResult,
    action_intents: tuple[ActionIntent, ...],
) -> ControlledStrategyResult:
    return ControlledStrategyResult(
        strategy_name=strategy_name,
        valid=result.valid,
        observer_only=True,
        execution_allowed=False,
        total_cost=result.total_cost,
        total_grid_import_kwh=result.total_grid_import_kwh,
        total_grid_export_kwh=result.total_grid_export_kwh,
        final_soc_kwh=result.final_soc_kwh,
        min_soc_kwh=result.min_soc_kwh,
        max_soc_kwh=result.max_soc_kwh,
        action_intent_count=len(action_intents),
        action_types=tuple(intent.action_type for intent in action_intents),
        reason_codes=result.reason_codes + result.errors,
    )


def _invalid_strategy_result(
    strategy_name: str,
    reason_codes: tuple[str, ...],
) -> ControlledStrategyResult:
    return ControlledStrategyResult(
        strategy_name=strategy_name,
        valid=False,
        observer_only=True,
        execution_allowed=False,
        total_cost=0.0,
        total_grid_import_kwh=0.0,
        total_grid_export_kwh=0.0,
        final_soc_kwh=0.0,
        min_soc_kwh=0.0,
        max_soc_kwh=0.0,
        action_intent_count=0,
        action_types=(),
        reason_codes=reason_codes,
    )


def _clean_error(exc: BaseException) -> str:
    text = str(exc).strip("'")
    return text or exc.__class__.__name__


__all__ = [
    "ControlledStrategyReplayResult",
    "ControlledStrategyResult",
    "run_controlled_strategy_replay",
]
