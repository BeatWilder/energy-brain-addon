from __future__ import annotations

from pathlib import Path

from app.v2160.planner_quality_scenarios import REQUIRED_SCENARIO_NAMES, get_planner_quality_scenarios
from app.v2161.scenario_pack_runner import run_planner_quality_scenario_pack


def test_scenario_pack_contains_all_required_scenario_names():
    scenarios = get_planner_quality_scenarios()

    assert tuple(scenario.scenario_name for scenario in scenarios) == REQUIRED_SCENARIO_NAMES


def test_every_scenario_fixture_has_at_least_four_slots():
    for scenario in get_planner_quality_scenarios():
        assert scenario.fixture["schema_version"] == "v2160_planner_quality_scenario"
        assert len(scenario.fixture["slots"]) >= 4


def test_run_scenario_pack_returns_observer_only_and_no_execution():
    result = run_planner_quality_scenario_pack()

    assert result.observer_only is True
    assert result.execution_allowed is False
    assert result.valid is True


def test_no_scenario_result_allows_execution():
    result = run_planner_quality_scenario_pack()

    assert all(scenario.execution_allowed is False for scenario in result.scenario_results)
    assert all(scenario.observer_only is True for scenario in result.scenario_results)


def test_all_required_scenarios_produce_a_result():
    result = run_planner_quality_scenario_pack()

    assert tuple(scenario.scenario_name for scenario in result.scenario_results) == REQUIRED_SCENARIO_NAMES
    assert result.passed_count == len(REQUIRED_SCENARIO_NAMES)
    assert result.failed_count == 0


def test_negative_prices_scenario_is_valid_and_remains_no_dispatch():
    scenario = _scenario_result("negative_prices")

    assert scenario.valid is True
    assert scenario.execution_allowed is False
    assert "no dispatch" in scenario.summary_markdown


def test_flat_prices_scenario_has_deterministic_best_strategy():
    first = _scenario_result("flat_prices")
    second = _scenario_result("flat_prices")

    assert first.best_strategy_name == "baseline_self_consumption"
    assert first.best_strategy_name == second.best_strategy_name
    assert first.summary_markdown == second.summary_markdown


def test_full_battery_scenario_final_soc_does_not_exceed_max_soc():
    scenario = _scenario_result("full_battery")
    fixture = _scenario_fixture("full_battery")

    assert scenario.final_soc_kwh <= fixture["battery"]["max_soc_kwh"]


def test_empty_battery_scenario_final_soc_does_not_go_below_floor():
    scenario = _scenario_result("empty_battery")
    fixture = _scenario_fixture("empty_battery")
    floor = max(fixture["battery"]["min_soc_kwh"], fixture["battery"]["reserve_kwh"])

    assert scenario.min_soc_kwh >= floor
    assert scenario.final_soc_kwh >= floor


def test_reserve_reached_scenario_does_not_discharge_below_reserve():
    scenario = _scenario_result("reserve_reached")
    fixture = _scenario_fixture("reserve_reached")

    assert scenario.min_soc_kwh >= fixture["battery"]["reserve_kwh"]


def test_high_pv_scenario_produces_non_empty_slot_traces():
    scenario = _scenario_result("high_pv")

    assert scenario.valid is True
    assert scenario.slot_line_count > 0
    assert "pv_surplus" in scenario.summary_markdown


def test_no_pv_scenario_produces_non_empty_audit():
    scenario = _scenario_result("no_pv")

    assert scenario.valid is True
    assert scenario.total_strategy_count == 4
    assert scenario.slot_line_count > 0


def test_high_load_scenario_remains_valid_and_safe():
    scenario = _scenario_result("high_load")

    assert scenario.valid is True
    assert scenario.execution_allowed is False
    assert scenario.best_strategy_name is not None


def test_export_opportunity_scenario_evaluates_export_aware_path():
    scenario = _scenario_result("export_opportunity")

    assert scenario.valid is True
    assert "export_aware_controlled" in scenario.summary_markdown
    assert "export_candidate" in scenario.summary_markdown


def test_charge_opportunity_scenario_evaluates_cheapest_charge_path():
    scenario = _scenario_result("charge_opportunity")

    assert scenario.valid is True
    assert "cheapest_window_charge_controlled" in scenario.summary_markdown
    assert "grid_charge_candidate" in scenario.summary_markdown


def test_scenario_pack_output_ordering_is_deterministic():
    first = run_planner_quality_scenario_pack()
    second = run_planner_quality_scenario_pack()

    assert first == second


def test_no_runtime_write_or_command_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2160/__init__.py"),
        Path("app/v2160/planner_quality_scenarios.py"),
        Path("app/v2161/__init__.py"),
        Path("app/v2161/scenario_pack_runner.py"),
        Path("docs/v2160_v2191_planner_quality_scenario_pack.md"),
        Path("tests/test_v2160_v2191_planner_quality_scenario_pack.py"),
        Path("tools/run_v2160_v2191_planner_quality_scenario_pack_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def _scenario_result(name: str):
    result = run_planner_quality_scenario_pack()
    matches = [scenario for scenario in result.scenario_results if scenario.scenario_name == name]
    assert len(matches) == 1
    return matches[0]


def _scenario_fixture(name: str):
    matches = [scenario for scenario in get_planner_quality_scenarios() if scenario.scenario_name == name]
    assert len(matches) == 1
    return matches[0].fixture


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
