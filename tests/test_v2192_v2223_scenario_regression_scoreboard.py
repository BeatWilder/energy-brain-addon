from __future__ import annotations

from pathlib import Path

from app.v2160.planner_quality_scenarios import REQUIRED_SCENARIO_NAMES
from app.v2193.scenario_regression_scoreboard import build_scenario_regression_scoreboard


def test_scoreboard_contains_all_required_scenario_names():
    scoreboard = build_scenario_regression_scoreboard()

    assert tuple(row.scenario_name for row in scoreboard.rows) == REQUIRED_SCENARIO_NAMES


def test_scoreboard_observer_only_true():
    scoreboard = build_scenario_regression_scoreboard()

    assert scoreboard.observer_only is True


def test_scoreboard_execution_allowed_false():
    scoreboard = build_scenario_regression_scoreboard()

    assert scoreboard.execution_allowed is False


def test_every_row_execution_allowed_false():
    scoreboard = build_scenario_regression_scoreboard()

    assert all(row.execution_allowed is False for row in scoreboard.rows)
    assert all(row.observer_only is True for row in scoreboard.rows)


def test_row_ordering_is_deterministic():
    scoreboard = build_scenario_regression_scoreboard()

    assert [row.scenario_name for row in scoreboard.rows] == list(REQUIRED_SCENARIO_NAMES)


def test_repeated_build_produces_identical_rows():
    first = build_scenario_regression_scoreboard()
    second = build_scenario_regression_scoreboard()

    assert first.rows == second.rows
    assert first.summary_markdown == second.summary_markdown


def test_passed_count_plus_failed_count_equals_row_count():
    scoreboard = build_scenario_regression_scoreboard()

    assert scoreboard.passed_count + scoreboard.failed_count == len(scoreboard.rows)


def test_every_valid_row_has_strategy_count():
    scoreboard = build_scenario_regression_scoreboard()

    assert all(row.strategy_count > 0 for row in scoreboard.rows if row.valid)


def test_every_valid_row_has_slot_line_count():
    scoreboard = build_scenario_regression_scoreboard()

    assert all(row.slot_line_count > 0 for row in scoreboard.rows if row.valid)


def test_every_row_has_regression_reason_codes_tuple():
    scoreboard = build_scenario_regression_scoreboard()

    assert all(isinstance(row.regression_reason_codes, tuple) for row in scoreboard.rows)
    assert all(row.regression_reason_codes for row in scoreboard.rows)


def test_negative_prices_row_exists():
    assert _row("negative_prices").scenario_name == "negative_prices"


def test_flat_prices_row_exists():
    assert _row("flat_prices").scenario_name == "flat_prices"


def test_full_battery_row_exists():
    assert _row("full_battery").scenario_name == "full_battery"


def test_empty_battery_row_exists():
    assert _row("empty_battery").scenario_name == "empty_battery"


def test_reserve_reached_row_exists():
    assert _row("reserve_reached").scenario_name == "reserve_reached"


def test_high_pv_row_exists():
    assert _row("high_pv").scenario_name == "high_pv"


def test_no_pv_row_exists():
    assert _row("no_pv").scenario_name == "no_pv"


def test_high_load_row_exists():
    assert _row("high_load").scenario_name == "high_load"


def test_export_opportunity_row_exists():
    assert _row("export_opportunity").scenario_name == "export_opportunity"


def test_charge_opportunity_row_exists():
    assert _row("charge_opportunity").scenario_name == "charge_opportunity"


def test_markdown_contains_required_sections_and_safety_notes():
    scoreboard = build_scenario_regression_scoreboard()
    markdown = scoreboard.summary_markdown

    assert "# Scenario Regression Scoreboard" in markdown
    assert "## Safety" in markdown
    assert "## Summary" in markdown
    assert "## Rows" in markdown
    assert "no dispatch" in markdown
    assert "no Home Assistant writes" in markdown


def test_scoreboard_rows_include_cost_import_export_values():
    scoreboard = build_scenario_regression_scoreboard()

    assert all(isinstance(row.total_cost, float) for row in scoreboard.rows)
    assert all(isinstance(row.total_grid_import_kwh, float) for row in scoreboard.rows)
    assert all(isinstance(row.total_grid_export_kwh, float) for row in scoreboard.rows)


def test_no_runtime_write_or_command_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2192/__init__.py"),
        Path("app/v2192/scenario_regression_scoreboard_contract.py"),
        Path("app/v2193/__init__.py"),
        Path("app/v2193/scenario_regression_scoreboard.py"),
        Path("docs/v2192_v2223_scenario_regression_scoreboard.md"),
        Path("tests/test_v2192_v2223_scenario_regression_scoreboard.py"),
        Path("tools/run_v2192_v2223_scenario_regression_scoreboard_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def _row(name: str):
    scoreboard = build_scenario_regression_scoreboard()
    matches = [row for row in scoreboard.rows if row.scenario_name == name]
    assert len(matches) == 1
    return matches[0]


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
