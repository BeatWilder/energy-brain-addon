"""Typed contract for offline planner replay audit reports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StrategyAuditLine:
    strategy_name: str
    is_winner: bool
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
    audit_reason: str


@dataclass(frozen=True)
class SlotAuditLine:
    strategy_name: str
    slot_index: int
    action_type: str
    soc_start_kwh: float
    soc_end_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    slot_cost: float
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PlannerReplayAuditReport:
    valid: bool
    observer_only: bool
    execution_allowed: bool
    best_strategy_name: str | None
    winning_reason_codes: tuple[str, ...]
    losing_reason_codes: tuple[tuple[str, tuple[str, ...]], ...]
    strategy_lines: tuple[StrategyAuditLine, ...]
    slot_lines: tuple[SlotAuditLine, ...]
    summary_markdown: str
    reason_codes: tuple[str, ...] = field(default_factory=lambda: ("observer_only_no_execution",))


__all__ = [
    "PlannerReplayAuditReport",
    "SlotAuditLine",
    "StrategyAuditLine",
]
