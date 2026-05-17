from __future__ import annotations

import subprocess
from pathlib import Path

from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2065.controlled_action_simulator import simulate_controlled_actions
from app.v2096.strategy_action_intent_builder import (
    build_baseline_action_intents,
    build_cheapest_window_charge_intents,
    build_export_aware_intents,
    build_hold_reserve_intents,
)
from app.v2097.controlled_strategy_replay import run_controlled_strategy_replay


def test_baseline_strategy_creates_deterministic_no_command_replay():
    first = run_controlled_strategy_replay(_fixture())
    second = run_controlled_strategy_replay(_fixture())
    baseline = first.strategy_results[0]

    assert first == second
    assert baseline.strategy_name == "baseline_self_consumption"
    assert baseline.action_intent_count == 0
    assert baseline.action_types == ()
    assert baseline.execution_allowed is False
    assert baseline.observer_only is True


def test_controlled_replay_returns_exactly_four_strategy_results():
    result = run_controlled_strategy_replay(_fixture())

    assert result.valid is True
    assert [strategy.strategy_name for strategy in result.strategy_results] == [
        "baseline_self_consumption",
        "cheapest_window_charge_controlled",
        "export_aware_controlled",
        "hold_reserve_controlled",
    ]
    assert len(result.strategy_results) == 4


def test_all_strategy_results_stay_observer_only_without_execution():
    result = run_controlled_strategy_replay(_fixture())

    assert result.execution_allowed is False
    assert result.observer_only is True
    assert all(strategy.execution_allowed is False for strategy in result.strategy_results)
    assert all(strategy.observer_only is True for strategy in result.strategy_results)


def test_cheapest_strategy_selects_cheapest_import_slot_deterministically():
    loaded = build_simulation_input(_fixture(import_prices=(0.30, 0.10, 0.20)))
    assert loaded.simulation_input is not None

    intents = build_cheapest_window_charge_intents(loaded.simulation_input, 1.0)

    assert len(intents) == 1
    assert intents[0].slot_index == 1
    assert intents[0].action_type == "grid_charge_candidate"


def test_cheapest_strategy_tie_breaks_by_lowest_slot_index():
    loaded = build_simulation_input(_fixture(import_prices=(0.10, 0.10, 0.20)))
    assert loaded.simulation_input is not None

    intents = build_cheapest_window_charge_intents(loaded.simulation_input, 1.0)

    assert [intent.slot_index for intent in intents] == [0]


def test_export_strategy_selects_highest_export_slot_deterministically():
    loaded = build_simulation_input(_fixture(export_prices=(0.05, 0.40, 0.20), initial_soc=8.0))
    assert loaded.simulation_input is not None

    intents = build_export_aware_intents(loaded.simulation_input, 1.0)

    assert len(intents) == 1
    assert intents[0].slot_index == 1
    assert intents[0].action_type == "export_candidate"


def test_export_strategy_tie_breaks_by_lowest_slot_index():
    loaded = build_simulation_input(_fixture(export_prices=(0.40, 0.40, 0.20), initial_soc=8.0))
    assert loaded.simulation_input is not None

    intents = build_export_aware_intents(loaded.simulation_input, 1.0)

    assert [intent.slot_index for intent in intents] == [0]


def test_non_positive_requested_energy_returns_no_action_intents():
    loaded = build_simulation_input(_fixture())
    assert loaded.simulation_input is not None

    assert build_cheapest_window_charge_intents(loaded.simulation_input, 0.0) == ()
    assert build_export_aware_intents(loaded.simulation_input, -1.0) == ()


def test_hold_strategy_creates_hold_candidates_for_deterministic_matching_slots():
    loaded = build_simulation_input(_fixture(loads=(0.5, 2.0, 3.0), pvs=(1.0, 1.0, 3.5)))
    assert loaded.simulation_input is not None

    intents = build_hold_reserve_intents(loaded.simulation_input)

    assert [intent.slot_index for intent in intents] == [1]
    assert [intent.action_type for intent in intents] == ["hold_candidate"]


def test_invalid_fixture_fails_safe():
    fixture = _fixture()
    fixture["observer_only"] = False
    result = run_controlled_strategy_replay(fixture)

    assert result.valid is False
    assert result.execution_allowed is False
    assert result.observer_only is True
    assert result.best_strategy_name is None
    assert len(result.strategy_results) == 4
    assert "observer_only_required" in result.reason_codes


def test_best_strategy_name_is_deterministic_when_costs_tie():
    fixture = _fixture(initial_soc=10.0, max_soc=10.0, discharge_power=0.0, loads=(0.0, 0.0, 0.0))
    result = run_controlled_strategy_replay(fixture)

    assert result.best_strategy_name == "baseline_self_consumption"
    assert [strategy.total_cost for strategy in result.strategy_results] == [0.0, 0.0, 0.0, 0.0]


def test_controlled_replay_uses_v2065_simulator_outputs():
    fixture = _fixture(import_prices=(0.50, 0.10, 0.20), initial_soc=2.0, loads=(0.0, 0.0, 0.0))
    loaded = build_simulation_input(fixture)
    assert loaded.simulation_input is not None
    expected_intents = build_cheapest_window_charge_intents(loaded.simulation_input, 1.0)
    expected = simulate_controlled_actions(loaded.simulation_input, expected_intents)

    replay = run_controlled_strategy_replay(fixture)
    cheapest = replay.strategy_results[1]

    assert cheapest.action_intent_count == 1
    assert cheapest.action_types == ("grid_charge_candidate",)
    assert cheapest.total_grid_import_kwh == expected.total_grid_import_kwh
    assert cheapest.final_soc_kwh == expected.final_soc_kwh
    assert "controlled_action_intent_simulation" in cheapest.reason_codes


def test_no_strategy_can_push_soc_outside_min_or_max():
    fixture = _fixture(initial_soc=9.8, max_soc=10.0, loads=(0.0, 2.0, 0.0), pvs=(0.0, 0.0, 0.0))
    result = run_controlled_strategy_replay(fixture)

    for strategy in result.strategy_results:
        assert strategy.min_soc_kwh >= 1.0
        assert strategy.max_soc_kwh <= 10.0


def test_no_strategy_can_discharge_below_reserve():
    fixture = _fixture(initial_soc=1.2, reserve=1.0, loads=(3.0, 3.0, 3.0), export_prices=(0.50, 0.40, 0.30))
    result = run_controlled_strategy_replay(fixture)

    assert all(strategy.min_soc_kwh >= 1.0 for strategy in result.strategy_results)


def test_output_ordering_is_deterministic():
    first = run_controlled_strategy_replay(_fixture())
    second = run_controlled_strategy_replay(_fixture())

    assert first.strategy_results == second.strategy_results
    assert [strategy.strategy_name for strategy in first.strategy_results] == [
        strategy.strategy_name for strategy in second.strategy_results
    ]


def test_no_runtime_write_or_command_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2096/__init__.py"),
        Path("app/v2096/strategy_action_intent_builder.py"),
        Path("app/v2097/__init__.py"),
        Path("app/v2097/controlled_strategy_replay.py"),
        Path("docs/v2096_v2127_controlled_strategy_replay_integration.md"),
        Path("tests/test_v2096_v2127_controlled_strategy_replay_integration.py"),
        Path("tools/run_v2096_v2127_controlled_strategy_replay_integration_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def test_protected_dirty_files_are_not_part_of_this_change():
    protected = [
        "config.yaml",
        "energy_brain/web_ui.py",
        "energy_brain/ui_static/fresh_home_v1.py",
        "energy_brain/ui_static/fresh_home_v2.py",
        "energy_brain/ui_static/ha_powerflow_card.py",
        "energy_brain/ui_static/powerflow_v2.py",
        "tests/test_web_ui.py",
        "energy_brain_v5.py",
    ]
    result = subprocess.run(["git", "diff", "--", *protected], check=True, capture_output=True, text=True)

    assert "app/v2096" not in result.stdout
    assert "app/v2097" not in result.stdout
    assert "v2096_v2127" not in result.stdout


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
