from __future__ import annotations

import subprocess
from pathlib import Path

from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2033.strategy_comparison import compare_strategies


def test_fixture_builds_valid_simulation_input():
    loaded = build_simulation_input(_fixture())

    assert loaded.valid is True
    assert loaded.simulation_input is not None
    assert loaded.simulation_input.observer_only is True
    assert loaded.simulation_input.slots[0].slot_id == "cheap"
    assert loaded.simulation_input.battery.capacity_kwh == 10.0


def test_comparison_returns_exactly_three_strategies():
    comparison = compare_strategies(_fixture())

    assert [score.strategy_name for score in comparison.scores] == [
        "baseline_self_consumption",
        "cheapest_window_charge",
        "export_aware_placeholder",
    ]


def test_all_strategies_execution_allowed_false():
    comparison = compare_strategies(_fixture())

    assert [score.execution_allowed for score in comparison.scores] == [False, False, False]


def test_baseline_has_valid_simulation_result():
    baseline = _score("baseline_self_consumption", compare_strategies(_fixture()))

    assert baseline.valid is True
    assert baseline.total_grid_import_kwh >= 0.0
    assert baseline.total_grid_export_kwh >= 0.0
    assert baseline.final_soc_kwh >= 0.0
    assert "offline_self_consumption_simulation" in baseline.reason_codes


def test_cheapest_window_strategy_identifies_cheapest_slot_deterministically():
    cheapest = _score("cheapest_window_charge", compare_strategies(_fixture()))

    assert cheapest.valid is True
    assert cheapest.candidate_slot_ids == ("cheap",)
    assert cheapest.action_change_count == 0
    assert "candidate_window_only" in cheapest.reason_codes


def test_export_aware_placeholder_identifies_highest_export_slot_deterministically():
    export_aware = _score("export_aware_placeholder", compare_strategies(_fixture()))

    assert export_aware.valid is True
    assert export_aware.candidate_slot_ids == ("export-a",)
    assert export_aware.action_change_count == 0
    assert "candidate_window_only" in export_aware.reason_codes


def test_invalid_fixture_fails_safe():
    comparison = compare_strategies({"observer_only": True, "slots": []})

    assert comparison.valid is False
    assert [score.valid for score in comparison.scores] == [False, False, False]
    assert [score.execution_allowed for score in comparison.scores] == [False, False, False]
    assert all("invalid_fixture_no_action" in score.reason_codes for score in comparison.scores)


def test_deterministic_ordering_and_tie_breaking():
    comparison = compare_strategies(_fixture_with_ties())

    assert [score.strategy_name for score in comparison.scores] == [
        "baseline_self_consumption",
        "cheapest_window_charge",
        "export_aware_placeholder",
    ]
    assert _score("cheapest_window_charge", comparison).candidate_slot_ids == ("a-cheap",)
    assert _score("export_aware_placeholder", comparison).candidate_slot_ids == ("a-export",)


def test_no_strategy_has_runtime_write_or_dispatch_surface():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2032/__init__.py"),
        Path("app/v2032/fixture_replay_contract.py"),
        Path("app/v2033/__init__.py"),
        Path("app/v2033/strategy_comparison.py"),
        Path("docs/v2032_v2063_fixture_replay_strategy_comparison.md"),
        Path("tests/test_v2032_v2063_fixture_replay_strategy_comparison.py"),
        Path("tools/run_v2032_v2063_fixture_replay_strategy_comparison_smoke.sh"),
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
    ]
    result = subprocess.run(["git", "diff", "--", *protected], check=True, capture_output=True, text=True)

    assert "app/v2032" not in result.stdout
    assert "app/v2033" not in result.stdout
    assert "v2032_v2063" not in result.stdout


def _score(strategy_name, comparison):
    matches = [score for score in comparison.scores if score.strategy_name == strategy_name]
    assert len(matches) == 1
    return matches[0]


def _fixture():
    return {
        "observer_only": True,
        "slots": [
            {
                "slot_id": "cheap",
                "pv_kwh": 0.0,
                "load_kwh": 1.0,
                "import_price_per_kwh": 0.10,
                "export_price_per_kwh": 0.02,
            },
            {
                "slot_id": "export-b",
                "pv_kwh": 3.0,
                "load_kwh": 1.0,
                "import_price_per_kwh": 0.25,
                "export_price_per_kwh": 0.40,
            },
            {
                "slot_id": "export-a",
                "pv_kwh": 4.0,
                "load_kwh": 1.0,
                "import_price_per_kwh": 0.30,
                "export_price_per_kwh": 0.40,
            },
        ],
        "battery": _battery(),
    }


def _fixture_with_ties():
    fixture = _fixture()
    fixture["slots"] = [
        {
            "slot_id": "b-cheap",
            "pv_kwh": 0.0,
            "load_kwh": 0.5,
            "import_price_per_kwh": 0.05,
            "export_price_per_kwh": 0.01,
        },
        {
            "slot_id": "a-cheap",
            "pv_kwh": 0.0,
            "load_kwh": 0.5,
            "import_price_per_kwh": 0.05,
            "export_price_per_kwh": 0.01,
        },
        {
            "slot_id": "b-export",
            "pv_kwh": 2.0,
            "load_kwh": 0.0,
            "import_price_per_kwh": 0.40,
            "export_price_per_kwh": 0.80,
        },
        {
            "slot_id": "a-export",
            "pv_kwh": 2.0,
            "load_kwh": 0.0,
            "import_price_per_kwh": 0.40,
            "export_price_per_kwh": 0.80,
        },
    ]
    return fixture


def _battery():
    return {
        "capacity_kwh": 10.0,
        "min_soc_kwh": 0.0,
        "max_soc_kwh": 10.0,
        "initial_soc_kwh": 5.0,
        "reserve_kwh": 1.0,
        "charge_power_kw": 5.0,
        "discharge_power_kw": 5.0,
        "round_trip_efficiency": 1.0,
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

