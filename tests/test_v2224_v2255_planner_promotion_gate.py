from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.v2160.planner_quality_scenarios import REQUIRED_SCENARIO_NAMES
from app.v2192.scenario_regression_scoreboard_contract import (
    ScenarioRegressionScoreboard,
    ScenarioScoreboardRow,
)
from app.v2193.scenario_regression_scoreboard import build_scenario_regression_scoreboard
from app.v2224.planner_promotion_gate_contract import ALLOWED_PROMOTION_DECISIONS
from app.v2225.planner_promotion_gate import (
    build_planner_promotion_gate,
    evaluate_planner_promotion_gate,
)


def test_all_scenarios_pass_accepts_for_shadow():
    decision = build_planner_promotion_gate()

    assert decision.decision == "accepted_for_shadow"
    assert decision.accepted_for_shadow is True
    assert "promotion_gate_accepted_for_shadow" in decision.reason_codes


def test_one_non_critical_regression_needs_review():
    scoreboard = build_scenario_regression_scoreboard()
    rows = list(scoreboard.rows)
    rows[0] = replace(
        rows[0],
        valid=False,
        safety_passed=False,
        regression_reason_codes=("cost_regression_needs_review",),
    )
    synthetic = replace(scoreboard, rows=tuple(rows), passed_count=len(rows) - 1, failed_count=1, valid=True)

    decision = evaluate_planner_promotion_gate(synthetic)

    assert decision.decision == "needs_review"
    assert decision.accepted_for_shadow is False
    assert "promotion_gate_needs_review" in decision.reason_codes


def test_soc_or_reserve_violation_is_rejected():
    scoreboard = build_scenario_regression_scoreboard()
    rows = list(scoreboard.rows)
    rows[0] = replace(
        rows[0],
        valid=False,
        safety_passed=False,
        regression_reason_codes=("scenario_min_soc_below_reserve",),
    )
    synthetic = replace(scoreboard, rows=tuple(rows), passed_count=len(rows) - 1, failed_count=1, valid=False)

    decision = evaluate_planner_promotion_gate(synthetic)

    assert decision.decision == "rejected"
    assert decision.accepted_for_shadow is False
    assert "scenario_min_soc_below_reserve" in decision.audit_summary.critical_reason_codes


def test_missing_scoreboard_is_rejected():
    decision = evaluate_planner_promotion_gate(None)

    assert decision.decision == "rejected"
    assert decision.accepted_for_shadow is False
    assert "scoreboard_required" in decision.reason_codes


def test_missing_required_scenario_is_not_accepted():
    scoreboard = build_scenario_regression_scoreboard()
    synthetic = replace(
        scoreboard,
        rows=scoreboard.rows[:-1],
        passed_count=len(scoreboard.rows) - 1,
        failed_count=0,
        valid=True,
    )

    decision = evaluate_planner_promotion_gate(synthetic)

    assert decision.decision in ("needs_review", "rejected")
    assert decision.accepted_for_shadow is False
    assert decision.decision != "accepted_for_shadow"


def test_flat_price_scenario_included():
    decision = build_planner_promotion_gate()

    assert "flat_prices" in _scenario_names(decision)


def test_negative_price_scenario_included():
    decision = build_planner_promotion_gate()

    assert "negative_prices" in _scenario_names(decision)


def test_high_pv_scenario_included():
    decision = build_planner_promotion_gate()

    assert "high_pv" in _scenario_names(decision)


def test_high_load_scenario_included():
    decision = build_planner_promotion_gate()

    assert "high_load" in _scenario_names(decision)


def test_empty_battery_and_reserve_reached_cases_included():
    decision = build_planner_promotion_gate()
    names = _scenario_names(decision)

    assert "empty_battery" in names
    assert "reserve_reached" in names


def test_execution_allowed_is_always_false():
    accepted = build_planner_promotion_gate()
    rejected = evaluate_planner_promotion_gate(None)

    assert accepted.execution_allowed is False
    assert rejected.execution_allowed is False


def test_observer_only_is_always_true():
    accepted = build_planner_promotion_gate()
    rejected = evaluate_planner_promotion_gate(None)

    assert accepted.observer_only is True
    assert rejected.observer_only is True


def test_allowed_decision_values_are_fixed():
    assert ALLOWED_PROMOTION_DECISIONS == ("accepted_for_shadow", "needs_review", "rejected")


def test_gate_rejects_missing_safety_evidence():
    row = ScenarioScoreboardRow(
        scenario_name="negative_prices",
        expected_focus="negative price handling",
        best_strategy_name="baseline_self_consumption",
        valid=True,
        observer_only=True,
        execution_allowed=False,
        total_cost=0.0,
        total_grid_import_kwh=0.0,
        total_grid_export_kwh=0.0,
        min_soc_kwh=1.0,
        final_soc_kwh=1.0,
        strategy_count=4,
        slot_line_count=4,
        safety_passed=False,
        regression_reason_codes=("missing_safety_evidence",),
        notes="synthetic",
    )
    scoreboard = ScenarioRegressionScoreboard(
        valid=True,
        observer_only=True,
        execution_allowed=False,
        rows=(row,),
        passed_count=0,
        failed_count=1,
        summary_markdown="synthetic",
        reason_codes=("synthetic_scoreboard",),
    )

    decision = evaluate_planner_promotion_gate(scoreboard)

    assert decision.decision == "rejected"
    assert "missing_safety_evidence" in decision.audit_summary.critical_reason_codes


def test_no_runtime_write_or_command_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2224/__init__.py"),
        Path("app/v2224/planner_promotion_gate_contract.py"),
        Path("app/v2225/__init__.py"),
        Path("app/v2225/planner_promotion_gate.py"),
        Path("docs/v2224_v2255_planner_promotion_gate.md"),
        Path("tests/test_v2224_v2255_planner_promotion_gate.py"),
        Path("tools/run_v2224_v2255_planner_promotion_gate_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def test_required_scenario_notes_match_required_order():
    decision = build_planner_promotion_gate()

    assert tuple(note.scenario_name for note in decision.scenario_notes) == REQUIRED_SCENARIO_NAMES


def _scenario_names(decision):
    return {note.scenario_name for note in decision.scenario_notes}


def _forbidden_terms() -> list[str]:
    pieces = [
        ("call", "_", "service"),
        ("set", "_", "state"),
        ("req", "uests"),
        ("aio", "http"),
        ("m", "qtt"),
        ("pa", "ho"),
        ("Alpha", "ESS"),
        ("home", "assistant"),
        ("hass", "."),
        ("write", "_", "and", "_", "poll"),
        ("rest", "_", "set"),
        ("rest", "_", "post"),
        ("rest", "_", "get"),
    ]
    return ["".join(piece) for piece in pieces]
