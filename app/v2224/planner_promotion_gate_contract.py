"""Typed contract for offline planner promotion gate decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.v2160.planner_quality_scenarios import REQUIRED_SCENARIO_NAMES


ALLOWED_PROMOTION_DECISIONS = (
    "accepted_for_shadow",
    "needs_review",
    "rejected",
)


@dataclass(frozen=True)
class PlannerPromotionConfig:
    required_scenario_names: tuple[str, ...] = REQUIRED_SCENARIO_NAMES
    minimum_pass_count: int = len(REQUIRED_SCENARIO_NAMES)
    maximum_allowed_failures: int = 0
    review_failure_limit: int = 1
    regression_score_threshold: float = 1.0


@dataclass(frozen=True)
class PlannerPromotionAuditSummary:
    scenario_count: int
    passed_count: int
    failed_count: int
    regression_score: float
    required_scenario_count: int
    missing_required_scenarios: tuple[str, ...]
    critical_reason_codes: tuple[str, ...]
    review_reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class PlannerPromotionScenarioNote:
    scenario_name: str
    safety_passed: bool
    valid: bool
    best_strategy_name: str | None
    reason_codes: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class PlannerPromotionDecision:
    decision: str
    accepted_for_shadow: bool
    observer_only: bool
    execution_allowed: bool
    reason_codes: tuple[str, ...]
    audit_summary: PlannerPromotionAuditSummary
    scenario_notes: tuple[PlannerPromotionScenarioNote, ...]


def validate_promotion_decision_value(decision: str) -> bool:
    """Return whether the decision string is an allowed offline gate value."""

    return decision in ALLOWED_PROMOTION_DECISIONS


__all__ = [
    "ALLOWED_PROMOTION_DECISIONS",
    "PlannerPromotionAuditSummary",
    "PlannerPromotionConfig",
    "PlannerPromotionDecision",
    "PlannerPromotionScenarioNote",
    "validate_promotion_decision_value",
]
