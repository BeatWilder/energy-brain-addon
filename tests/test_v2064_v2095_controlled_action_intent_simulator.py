from __future__ import annotations

import subprocess
from pathlib import Path

from app.v2001.canonical_self_consumption_simulator import simulate_self_consumption
from app.v2032.fixture_replay_contract import build_simulation_input
from app.v2064.action_intent_contract import ActionIntent
from app.v2065.controlled_action_simulator import simulate_controlled_actions


def test_no_actions_matches_baseline_self_consumption_for_simple_fixture():
    loaded = build_simulation_input(_fixture())
    assert loaded.simulation_input is not None

    baseline = simulate_self_consumption(loaded.simulation_input)
    controlled = simulate_controlled_actions(loaded.simulation_input, [])

    assert controlled.valid is True
    assert controlled.total_grid_import_kwh == baseline.total_import_kwh
    assert controlled.total_grid_export_kwh == baseline.total_export_kwh
    assert controlled.total_cost == baseline.total_cost
    assert controlled.final_soc_kwh == baseline.final_soc_kwh
    assert [trace.soc_end_kwh for trace in controlled.trace] == [trace.soc_end_kwh for trace in baseline.trace]


def test_grid_charge_candidate_increases_soc_without_exceeding_max_soc():
    result = simulate_controlled_actions(
        _fixture(initial_soc=9.5, max_soc=10.0, charge_power=5.0),
        [ActionIntent(0, "grid_charge_candidate", 2.0, ("cheap_grid_slot",))],
    )

    assert result.valid is True
    assert result.trace[0].soc_end_kwh == 10.0
    assert result.trace[0].grid_to_battery_kwh == 0.5
    assert result.max_soc_kwh == 10.0


def test_grid_charge_candidate_is_clipped_by_charge_power_and_duration():
    result = simulate_controlled_actions(
        _fixture(initial_soc=2.0, charge_power=1.0, duration=0.5),
        [ActionIntent(0, "grid_charge_candidate", 3.0)],
    )

    assert result.valid is True
    assert result.trace[0].grid_to_battery_kwh == 0.5
    assert result.trace[0].clipped_energy_kwh == 0.5
    assert result.trace[0].battery_charge_power_kw == 1.0


def test_export_candidate_decreases_soc_without_crossing_reserve():
    result = simulate_controlled_actions(
        _fixture(initial_soc=2.0, reserve=1.5, discharge_power=5.0),
        [ActionIntent(0, "export_candidate", 3.0)],
    )

    assert result.valid is True
    assert result.trace[0].battery_to_grid_kwh == 0.5
    assert result.trace[0].soc_end_kwh == 1.5
    assert result.min_soc_kwh == 1.5


def test_export_candidate_is_clipped_by_discharge_power_and_duration():
    result = simulate_controlled_actions(
        _fixture(initial_soc=8.0, reserve=1.0, discharge_power=1.0, duration=0.25),
        [ActionIntent(0, "export_candidate", 3.0)],
    )

    assert result.valid is True
    assert result.trace[0].battery_to_grid_kwh == 0.25
    assert result.trace[0].clipped_energy_kwh == 0.25
    assert result.trace[0].battery_discharge_power_kw == 1.0


def test_hold_candidate_prevents_battery_discharge_to_load():
    result = simulate_controlled_actions(
        _fixture(pv=0.0, load=2.0, initial_soc=6.0),
        [ActionIntent(0, "hold_candidate", 0.0)],
    )

    assert result.valid is True
    assert result.trace[0].load_served_by_battery_kwh == 0.0
    assert result.trace[0].load_served_by_grid_kwh == 2.0
    assert result.trace[0].soc_end_kwh == 6.0


def test_invalid_slot_index_fails_safe():
    result = simulate_controlled_actions(_fixture(), [ActionIntent(99, "self_consumption", 0.0)])

    assert result.valid is False
    assert result.execution_allowed is False
    assert result.trace == ()
    assert "action_intent_0_slot_index_out_of_range" in result.errors


def test_negative_requested_energy_fails_safe():
    result = simulate_controlled_actions(_fixture(), [ActionIntent(0, "grid_charge_candidate", -0.1)])

    assert result.valid is False
    assert result.execution_allowed is False
    assert result.trace == ()
    assert "action_intent_0_requested_energy_must_be_non_negative" in result.errors


def test_unknown_action_type_and_missing_input_fail_safe():
    unknown = simulate_controlled_actions(_fixture(), [ActionIntent(0, "run_real_device", 1.0)])
    missing = simulate_controlled_actions(None, [])

    assert unknown.valid is False
    assert unknown.execution_allowed is False
    assert "action_intent_0_unknown_action_type" in unknown.errors
    assert missing.valid is False
    assert missing.execution_allowed is False
    assert missing.errors == ("simulation_input_required",)


def test_all_results_have_execution_allowed_false_and_observer_only_true():
    valid = simulate_controlled_actions(_fixture(), [])
    invalid = simulate_controlled_actions(_fixture(), [ActionIntent(4, "self_consumption", 0.0)])

    assert valid.execution_allowed is False
    assert valid.observer_only is True
    assert invalid.execution_allowed is False
    assert invalid.observer_only is True


def test_no_runtime_write_or_dispatch_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2064/__init__.py"),
        Path("app/v2064/action_intent_contract.py"),
        Path("app/v2065/__init__.py"),
        Path("app/v2065/controlled_action_simulator.py"),
        Path("docs/v2064_v2095_controlled_action_intent_simulator.md"),
        Path("tests/test_v2064_v2095_controlled_action_intent_simulator.py"),
        Path("tools/run_v2064_v2095_controlled_action_intent_simulator_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def test_deterministic_output_ordering():
    result = simulate_controlled_actions(
        _two_slot_fixture(),
        [
            ActionIntent(1, "export_candidate", 0.5),
            ActionIntent(0, "grid_charge_candidate", 0.5),
        ],
    )

    assert result.valid is True
    assert [trace.slot_index for trace in result.trace] == [0, 1]
    assert [trace.slot_id for trace in result.trace] == ["s0", "s1"]
    assert [trace.action_type_applied for trace in result.trace] == [
        "grid_charge_candidate",
        "export_candidate",
    ]


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

    assert "app/v2064" not in result.stdout
    assert "app/v2065" not in result.stdout
    assert "v2064_v2095" not in result.stdout


def _fixture(
    *,
    pv: float = 0.0,
    load: float = 0.0,
    initial_soc: float = 5.0,
    reserve: float = 1.0,
    max_soc: float = 10.0,
    charge_power: float = 5.0,
    discharge_power: float = 5.0,
    duration: float = 1.0,
):
    return {
        "observer_only": True,
        "slots": [
            {
                "slot_id": "s0",
                "pv_kwh": pv,
                "load_kwh": load,
                "import_price_per_kwh": 0.20,
                "export_price_per_kwh": 0.05,
                "duration_hours": duration,
            }
        ],
        "battery": {
            "capacity_kwh": 10.0,
            "min_soc_kwh": 0.0,
            "max_soc_kwh": max_soc,
            "initial_soc_kwh": initial_soc,
            "reserve_kwh": reserve,
            "charge_power_kw": charge_power,
            "discharge_power_kw": discharge_power,
            "round_trip_efficiency": 1.0,
        },
    }


def _two_slot_fixture():
    fixture = _fixture()
    fixture["slots"] = [
        {
            "slot_id": "s0",
            "pv_kwh": 0.0,
            "load_kwh": 0.0,
            "import_price_per_kwh": 0.10,
            "export_price_per_kwh": 0.05,
            "duration_hours": 1.0,
        },
        {
            "slot_id": "s1",
            "pv_kwh": 0.0,
            "load_kwh": 0.0,
            "import_price_per_kwh": 0.30,
            "export_price_per_kwh": 0.40,
            "duration_hours": 1.0,
        },
    ]
    return fixture


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
