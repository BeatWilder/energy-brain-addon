"""Evaluate offline planner promotion readiness from scenario scoreboards."""

from __future__ import annotations

from app.v2193.scenario_regression_scoreboard import build_scenario_regression_scoreboard
from app.v2224.planner_promotion_gate_contract import (
    PlannerPromotionAuditSummary,
    PlannerPromotionConfig,
    PlannerPromotionDecision,
    PlannerPromotionScenarioNote,
)


CRITICAL_REASON_MARKERS = (
    "soc",
    "reserve",
    "execution",
    "observer",
    "missing_required",
    "missing_safety",
    "scoreboard_required",
    "scoreboard_invalid",
    "required_scenario_missing",
)


def build_planner_promotion_gate(
    config: PlannerPromotionConfig | None = None,
) -> PlannerPromotionDecision:
    """Build the current offline scoreboard and evaluate promotion readiness."""

    return evaluate_planner_promotion_gate(
        build_scenario_regression_scoreboard(),
        config=config,
    )


def evaluate_planner_promotion_gate(
    scoreboard: object | None,
    config: PlannerPromotionConfig | None = None,
) -> PlannerPromotionDecision:
    """Evaluate an explicit scoreboard shape with fail-safe promotion rules."""

    gate_config = config or PlannerPromotionConfig()
    if scoreboard is None:
        return _decision(
            decision="rejected",
            reason_codes=("scoreboard_required", "promotion_gate_rejected", "observer_only_no_execution"),
            audit_summary=_empty_audit_summary(gate_config, ("scoreboard_required",), ()),
            scenario_notes=(),
        )

    rows = tuple(getattr(scoreboard, "rows", ()) or ())
    scoreboard_reason_codes = tuple(getattr(scoreboard, "reason_codes", ()) or ())
    validation_codes = _scoreboard_validation_codes(scoreboard, rows, gate_config)
    scenario_notes = tuple(_scenario_note(row) for row in rows)
    passed_count = sum(1 for row in rows if bool(getattr(row, "safety_passed", False)))
    failed_count = len(rows) - passed_count
    regression_score = round(passed_count / len(rows), 6) if rows else 0.0

    row_failure_codes = tuple(
        reason_code
        for row in rows
        for reason_code in tuple(getattr(row, "regression_reason_codes", ()) or ())
        if reason_code != "regression_passed"
    )
    critical_codes = _critical_codes(validation_codes + row_failure_codes)
    review_codes = _review_codes(validation_codes + row_failure_codes, critical_codes)
    audit_summary = PlannerPromotionAuditSummary(
        scenario_count=len(rows),
        passed_count=passed_count,
        failed_count=failed_count,
        regression_score=regression_score,
        required_scenario_count=len(gate_config.required_scenario_names),
        missing_required_scenarios=_missing_required_scenarios(rows, gate_config),
        critical_reason_codes=critical_codes,
        review_reason_codes=review_codes,
    )

    if critical_codes:
        return _decision(
            decision="rejected",
            reason_codes=scoreboard_reason_codes + validation_codes + critical_codes + (
                "promotion_gate_rejected",
                "shadow_only_no_live_control",
            ),
            audit_summary=audit_summary,
            scenario_notes=scenario_notes,
        )

    if _accepted(rows, passed_count, failed_count, regression_score, gate_config):
        return _decision(
            decision="accepted_for_shadow",
            reason_codes=scoreboard_reason_codes + (
                "promotion_gate_accepted_for_shadow",
                "shadow_only_no_live_control",
                "observer_only_no_execution",
            ),
            audit_summary=audit_summary,
            scenario_notes=scenario_notes,
        )

    return _decision(
        decision="needs_review",
        reason_codes=scoreboard_reason_codes + validation_codes + review_codes + (
            "promotion_gate_needs_review",
            "shadow_only_no_live_control",
        ),
        audit_summary=audit_summary,
        scenario_notes=scenario_notes,
    )


def _scoreboard_validation_codes(
    scoreboard: object,
    rows: tuple[object, ...],
    config: PlannerPromotionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not bool(getattr(scoreboard, "observer_only", False)):
        reason_codes.append("scoreboard_observer_only_required")
    if bool(getattr(scoreboard, "execution_allowed", True)):
        reason_codes.append("scoreboard_execution_not_allowed")
    if not bool(getattr(scoreboard, "valid", False)):
        reason_codes.append("scoreboard_invalid")
    if not rows:
        reason_codes.append("scoreboard_rows_required")
    missing = _missing_required_scenarios(rows, config)
    reason_codes.extend(f"required_scenario_missing:{name}" for name in missing)
    if getattr(scoreboard, "passed_count", None) is None:
        reason_codes.append("scoreboard_pass_count_required")
    if getattr(scoreboard, "failed_count", None) is None:
        reason_codes.append("scoreboard_fail_count_required")

    for row in rows:
        name = str(getattr(row, "scenario_name", "unknown"))
        if getattr(row, "valid", None) is None:
            reason_codes.append(f"{name}:row_valid_required")
        if getattr(row, "safety_passed", None) is None:
            reason_codes.append(f"{name}:missing_safety_evidence")
        if bool(getattr(row, "execution_allowed", True)):
            reason_codes.append(f"{name}:execution_not_allowed")
        if not bool(getattr(row, "observer_only", False)):
            reason_codes.append(f"{name}:observer_only_required")
        if int(getattr(row, "strategy_count", 0) or 0) <= 0:
            reason_codes.append(f"{name}:strategy_count_required")
        if int(getattr(row, "slot_line_count", 0) or 0) <= 0:
            reason_codes.append(f"{name}:slot_line_count_required")
        if getattr(row, "min_soc_kwh", None) is None:
            reason_codes.append(f"{name}:min_soc_required")
        if getattr(row, "final_soc_kwh", None) is None:
            reason_codes.append(f"{name}:final_soc_required")

    return tuple(reason_codes)


def _accepted(
    rows: tuple[object, ...],
    passed_count: int,
    failed_count: int,
    regression_score: float,
    config: PlannerPromotionConfig,
) -> bool:
    return (
        bool(rows)
        and passed_count >= config.minimum_pass_count
        and failed_count <= config.maximum_allowed_failures
        and regression_score >= config.regression_score_threshold
    )


def _missing_required_scenarios(
    rows: tuple[object, ...],
    config: PlannerPromotionConfig,
) -> tuple[str, ...]:
    present = {str(getattr(row, "scenario_name", "")) for row in rows}
    return tuple(name for name in config.required_scenario_names if name not in present)


def _critical_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        reason_code
        for reason_code in reason_codes
        if any(marker in reason_code for marker in CRITICAL_REASON_MARKERS)
    )


def _review_codes(
    reason_codes: tuple[str, ...],
    critical_codes: tuple[str, ...],
) -> tuple[str, ...]:
    critical = set(critical_codes)
    return tuple(reason_code for reason_code in reason_codes if reason_code not in critical)


def _scenario_note(row: object) -> PlannerPromotionScenarioNote:
    return PlannerPromotionScenarioNote(
        scenario_name=str(getattr(row, "scenario_name", "unknown")),
        safety_passed=bool(getattr(row, "safety_passed", False)),
        valid=bool(getattr(row, "valid", False)),
        best_strategy_name=getattr(row, "best_strategy_name", None),
        reason_codes=tuple(getattr(row, "regression_reason_codes", ()) or ()),
        notes=str(getattr(row, "notes", "")),
    )


def _decision(
    *,
    decision: str,
    reason_codes: tuple[str, ...],
    audit_summary: PlannerPromotionAuditSummary,
    scenario_notes: tuple[PlannerPromotionScenarioNote, ...],
) -> PlannerPromotionDecision:
    return PlannerPromotionDecision(
        decision=decision,
        accepted_for_shadow=decision == "accepted_for_shadow",
        observer_only=True,
        execution_allowed=False,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        audit_summary=audit_summary,
        scenario_notes=scenario_notes,
    )


def _empty_audit_summary(
    config: PlannerPromotionConfig,
    critical_codes: tuple[str, ...],
    review_codes: tuple[str, ...],
) -> PlannerPromotionAuditSummary:
    return PlannerPromotionAuditSummary(
        scenario_count=0,
        passed_count=0,
        failed_count=0,
        regression_score=0.0,
        required_scenario_count=len(config.required_scenario_names),
        missing_required_scenarios=config.required_scenario_names,
        critical_reason_codes=critical_codes,
        review_reason_codes=review_codes,
    )


__all__ = [
    "build_planner_promotion_gate",
    "evaluate_planner_promotion_gate",
]
