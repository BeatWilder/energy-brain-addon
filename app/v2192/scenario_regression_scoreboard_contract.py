"""Typed contract for deterministic scenario regression scoreboards."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioScoreboardRow:
    scenario_name: str
    expected_focus: str
    best_strategy_name: str | None
    valid: bool
    observer_only: bool
    execution_allowed: bool
    total_cost: float
    total_grid_import_kwh: float
    total_grid_export_kwh: float
    min_soc_kwh: float
    final_soc_kwh: float
    strategy_count: int
    slot_line_count: int
    safety_passed: bool
    regression_reason_codes: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class ScenarioRegressionScoreboard:
    valid: bool
    observer_only: bool
    execution_allowed: bool
    rows: tuple[ScenarioScoreboardRow, ...]
    passed_count: int
    failed_count: int
    summary_markdown: str
    reason_codes: tuple[str, ...] = field(default_factory=lambda: ("observer_only_no_execution",))


__all__ = [
    "ScenarioRegressionScoreboard",
    "ScenarioScoreboardRow",
]
