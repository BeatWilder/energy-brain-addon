from __future__ import annotations

from pathlib import Path

from app.v2097.controlled_strategy_replay import run_controlled_strategy_replay
from app.v2129.planner_replay_audit_report import build_planner_replay_audit_report


def test_valid_fixture_produces_valid_audit_report():
    report = build_planner_replay_audit_report(_fixture())

    assert report.valid is True
    assert report.best_strategy_name is not None
    assert "planner_replay_audit_report" in report.reason_codes


def test_report_has_observer_only_true_and_execution_allowed_false():
    report = build_planner_replay_audit_report(_fixture())

    assert report.observer_only is True
    assert report.execution_allowed is False
    assert all(line.observer_only is True for line in report.strategy_lines)
    assert all(line.execution_allowed is False for line in report.strategy_lines)


def test_summary_markdown_contains_required_sections():
    report = build_planner_replay_audit_report(_fixture())

    assert "# Planner Replay Audit" in report.summary_markdown
    assert "## Safety" in report.summary_markdown
    assert "## Winner" in report.summary_markdown
    assert "## Strategy comparison" in report.summary_markdown
    assert "## Slot trace summary" in report.summary_markdown


def test_strategy_lines_contain_exactly_four_strategies():
    report = build_planner_replay_audit_report(_fixture())

    assert [line.strategy_name for line in report.strategy_lines] == [
        "baseline_self_consumption",
        "cheapest_window_charge_controlled",
        "export_aware_controlled",
        "hold_reserve_controlled",
    ]
    assert len(report.strategy_lines) == 4


def test_exactly_one_winner_when_replay_is_valid():
    report = build_planner_replay_audit_report(_fixture())

    assert sum(1 for line in report.strategy_lines if line.is_winner) == 1


def test_winning_strategy_matches_replay_best_strategy_name():
    fixture = _fixture()
    replay = run_controlled_strategy_replay(fixture)
    report = build_planner_replay_audit_report(fixture)

    assert report.best_strategy_name == replay.best_strategy_name
    assert [line.strategy_name for line in report.strategy_lines if line.is_winner] == [replay.best_strategy_name]


def test_losing_strategies_get_deterministic_losing_reason_codes():
    report = build_planner_replay_audit_report(_fixture())
    losing = dict(report.losing_reason_codes)

    assert set(losing) == {
        "baseline_self_consumption",
        "cheapest_window_charge_controlled",
        "hold_reserve_controlled",
    }
    assert all(reasons for reasons in losing.values())
    assert all(
        reason in {"higher_cost_than_winner", "invalid_strategy_result", "tie_lost_by_strategy_order"}
        for reasons in losing.values()
        for reason in reasons
    )


def test_tie_behavior_is_deterministic_and_documented():
    fixture = _fixture(initial_soc=10.0, max_soc=10.0, discharge_power=0.0, loads=(0.0, 0.0, 0.0))
    report = build_planner_replay_audit_report(fixture)
    losing = dict(report.losing_reason_codes)

    assert report.best_strategy_name == "baseline_self_consumption"
    assert "deterministic_strategy_order_tie_break" in report.winning_reason_codes
    assert losing["cheapest_window_charge_controlled"] == ("tie_lost_by_strategy_order",)
    assert "deterministic_strategy_order_tie_break" in report.summary_markdown


def test_invalid_fixture_fails_safe_with_invalid_report():
    fixture = _fixture()
    fixture["observer_only"] = False
    report = build_planner_replay_audit_report(fixture)

    assert report.valid is False
    assert report.observer_only is True
    assert report.execution_allowed is False
    assert report.best_strategy_name is None
    assert report.slot_lines == ()
    assert "invalid replay" in report.summary_markdown


def test_slot_lines_are_deterministic_and_non_empty_for_valid_replay():
    first = build_planner_replay_audit_report(_fixture())
    second = build_planner_replay_audit_report(_fixture())

    assert first.slot_lines
    assert first.slot_lines == second.slot_lines


def test_slot_lines_include_action_type_and_soc_start_end():
    report = build_planner_replay_audit_report(_fixture())
    grid_charge_lines = [
        line for line in report.slot_lines if line.action_type == "grid_charge_candidate"
    ]

    assert grid_charge_lines
    assert all(isinstance(line.soc_start_kwh, float) for line in report.slot_lines)
    assert all(isinstance(line.soc_end_kwh, float) for line in report.slot_lines)


def test_no_strategy_audit_line_can_have_execution_allowed_true():
    report = build_planner_replay_audit_report(_fixture())

    assert all(line.execution_allowed is False for line in report.strategy_lines)


def test_markdown_contains_no_claim_of_real_execution_or_dispatch():
    report = build_planner_replay_audit_report(_fixture())
    text = report.summary_markdown.lower()

    assert "execution_allowed: false" in text
    assert "candidate simulation only" in text
    assert "dispatched" not in text
    assert "real execution" not in text


def test_no_runtime_write_or_command_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2128/__init__.py"),
        Path("app/v2128/planner_replay_audit_contract.py"),
        Path("app/v2129/__init__.py"),
        Path("app/v2129/planner_replay_audit_report.py"),
        Path("docs/v2128_v2159_planner_replay_audit_report.md"),
        Path("tests/test_v2128_v2159_planner_replay_audit_report.py"),
        Path("tools/run_v2128_v2159_planner_replay_audit_report_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def _fixture(
    *,
    import_prices: tuple[float, float, float] = (0.30, 0.10, 0.20),
    export_prices: tuple[float, float, float] = (0.05, 0.20, 0.10),
    loads: tuple[float, float, float] = (1.0, 1.0, 1.0),
    pvs: tuple[float, float, float] = (0.0, 0.0, 0.0),
    initial_soc: float = 5.0,
    reserve: float = 1.0,
    max_soc: float = 10.0,
    discharge_power: float = 5.0,
):
    return {
        "observer_only": True,
        "slots": [
            {
                "slot_id": f"s{index}",
                "pv_kwh": pvs[index],
                "load_kwh": loads[index],
                "import_price_per_kwh": import_prices[index],
                "export_price_per_kwh": export_prices[index],
                "duration_hours": 1.0,
            }
            for index in range(3)
        ],
        "battery": {
            "capacity_kwh": 10.0,
            "min_soc_kwh": 0.0,
            "max_soc_kwh": max_soc,
            "initial_soc_kwh": initial_soc,
            "reserve_kwh": reserve,
            "charge_power_kw": 5.0,
            "discharge_power_kw": discharge_power,
            "round_trip_efficiency": 1.0,
        },
    }


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
