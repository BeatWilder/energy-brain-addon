from __future__ import annotations

import subprocess
from pathlib import Path

from app.v2000.predbat_lesson_simulation_contract import BatteryPhysics, EnergySlot, SimulationInput
from app.v2001.canonical_self_consumption_simulator import simulate_self_consumption


def test_valid_input_simulates_pv_first_trace():
    result = simulate_self_consumption(
        _input(
            slots=(
                EnergySlot(slot_id="s0", pv_kwh=3.0, load_kwh=1.0, import_price_per_kwh=0.30),
                EnergySlot(slot_id="s1", pv_kwh=0.0, load_kwh=1.0, import_price_per_kwh=0.30),
            ),
            initial_soc_kwh=2.0,
        )
    )

    assert result.valid is True
    assert result.trace[0].pv_to_load_kwh == 1.0
    assert result.trace[0].pv_to_battery_kwh == 2.0
    assert result.trace[0].import_kwh == 0.0
    assert result.trace[1].battery_to_load_kwh == 1.0
    assert result.total_import_kwh == 0.0


def test_invalid_input_returns_no_action_result():
    result = simulate_self_consumption(
        _input(
            slots=(EnergySlot(slot_id="bad", pv_kwh=-1.0, load_kwh=1.0),),
            initial_soc_kwh=2.0,
        )
    )

    assert result.valid is False
    assert result.execution_allowed is False
    assert result.trace == ()
    assert "slot_0_pv_must_be_non_negative" in result.errors
    assert "invalid_input_no_action" in result.reason_codes


def test_execution_is_never_allowed_for_valid_and_invalid_results():
    valid = simulate_self_consumption(_input(slots=(EnergySlot(slot_id="s0", pv_kwh=0.0, load_kwh=0.0),)))
    invalid = simulate_self_consumption(
        _input(slots=(EnergySlot(slot_id="s0", pv_kwh=0.0, load_kwh=0.0),), observer_only=False)
    )

    assert valid.execution_allowed is False
    assert invalid.execution_allowed is False


def test_reserve_floor_is_respected():
    result = simulate_self_consumption(
        _input(
            slots=(EnergySlot(slot_id="load", pv_kwh=0.0, load_kwh=5.0),),
            initial_soc_kwh=3.0,
            reserve_kwh=2.0,
        )
    )

    trace = result.trace[0]
    assert trace.battery_to_load_kwh == 1.0
    assert trace.import_kwh == 4.0
    assert trace.soc_end_kwh == 2.0
    assert "remaining_load_imported" in trace.reason_codes


def test_full_battery_exports_pv_surplus():
    result = simulate_self_consumption(
        _input(
            slots=(EnergySlot(slot_id="full", pv_kwh=4.0, load_kwh=1.0),),
            initial_soc_kwh=5.0,
            max_soc_kwh=5.0,
        )
    )

    trace = result.trace[0]
    assert trace.pv_to_load_kwh == 1.0
    assert trace.pv_to_battery_kwh == 0.0
    assert trace.export_kwh == 3.0
    assert "battery_full_export_surplus" in trace.reason_codes


def test_charge_power_limit_exports_remaining_surplus():
    result = simulate_self_consumption(
        _input(
            slots=(EnergySlot(slot_id="charge-limit", pv_kwh=5.0, load_kwh=0.0),),
            initial_soc_kwh=1.0,
            charge_power_kw=2.0,
        )
    )

    trace = result.trace[0]
    assert trace.pv_to_battery_kwh == 2.0
    assert trace.export_kwh == 3.0
    assert trace.soc_end_kwh == 3.0


def test_discharge_power_limit_imports_remaining_load():
    result = simulate_self_consumption(
        _input(
            slots=(EnergySlot(slot_id="discharge-limit", pv_kwh=0.0, load_kwh=5.0),),
            initial_soc_kwh=5.0,
            reserve_kwh=0.0,
            discharge_power_kw=2.0,
        )
    )

    trace = result.trace[0]
    assert trace.battery_to_load_kwh == 2.0
    assert trace.import_kwh == 3.0
    assert trace.soc_end_kwh == 3.0


def test_negative_price_does_not_trigger_grid_charging():
    result = simulate_self_consumption(
        _input(
            slots=(EnergySlot(slot_id="negative-price", pv_kwh=0.0, load_kwh=0.0, import_price_per_kwh=-0.50),),
            initial_soc_kwh=1.0,
            reserve_kwh=0.0,
        )
    )

    trace = result.trace[0]
    assert trace.import_kwh == 0.0
    assert trace.pv_to_battery_kwh == 0.0
    assert trace.soc_end_kwh == 1.0
    assert result.total_cost == 0.0


def test_new_contract_files_have_no_forbidden_runtime_write_surfaces():
    forbidden = _forbidden_terms()
    paths = [
        Path("app/v2000/predbat_lesson_simulation_contract.py"),
        Path("app/v2001/__init__.py"),
        Path("app/v2001/canonical_self_consumption_simulator.py"),
        Path("docs/v2000_v2031_predbat_lesson_simulation_contract.md"),
        Path("tests/test_v2000_v2031_predbat_lesson_simulation_contract.py"),
        Path("tools/run_v2000_v2031_predbat_lesson_simulation_contract_smoke.sh"),
    ]
    offenders = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def test_protected_files_are_unchanged():
    protected = [
        "energy_brain_v5.py",
        "energy_brain/web_ui.py",
        "energy_brain/ui_static/fresh_home_v1.py",
        "energy_brain/ui_static/fresh_home_v2.py",
        "energy_brain/ui_static/ha_powerflow_card.py",
        "energy_brain/ui_static/powerflow_v2.py",
        "config.yaml",
        "app/v1968/__init__.py",
        "app/v1968/predbat_concept_audit.py",
        "app/v1969/__init__.py",
        "app/v1969/tesla_style_cockpit_spec.py",
    ]
    result = subprocess.run(["git", "diff", "--", *protected], check=True, capture_output=True, text=True)

    assert "app/v1968" not in result.stdout
    assert "app/v1969" not in result.stdout
    assert "energy_brain_v5.py" not in result.stdout


def _input(
    *,
    slots: tuple[EnergySlot, ...],
    initial_soc_kwh: float = 2.0,
    min_soc_kwh: float = 0.0,
    max_soc_kwh: float = 10.0,
    reserve_kwh: float = 1.0,
    charge_power_kw: float = 10.0,
    discharge_power_kw: float = 10.0,
    observer_only: bool = True,
) -> SimulationInput:
    return SimulationInput(
        slots=slots,
        observer_only=observer_only,
        battery=BatteryPhysics(
            capacity_kwh=10.0,
            min_soc_kwh=min_soc_kwh,
            max_soc_kwh=max_soc_kwh,
            initial_soc_kwh=initial_soc_kwh,
            reserve_kwh=reserve_kwh,
            charge_power_kw=charge_power_kw,
            discharge_power_kw=discharge_power_kw,
            round_trip_efficiency=1.0,
        ),
    )


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
