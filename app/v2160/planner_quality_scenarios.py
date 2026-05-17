"""Deterministic offline fixture scenarios for planner quality validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REQUIRED_SCENARIO_NAMES = (
    "negative_prices",
    "flat_prices",
    "full_battery",
    "empty_battery",
    "reserve_reached",
    "high_pv",
    "no_pv",
    "high_load",
    "export_opportunity",
    "charge_opportunity",
)


@dataclass(frozen=True)
class PlannerQualityScenario:
    scenario_name: str
    fixture: Mapping[str, Any]
    expected_focus: str
    expected_safe: bool
    notes: str
    required_reason_codes: tuple[str, ...] = ()


def get_planner_quality_scenarios() -> tuple[PlannerQualityScenario, ...]:
    """Return scenarios in deterministic validation order."""

    return (
        PlannerQualityScenario(
            scenario_name="negative_prices",
            fixture=_fixture(
                name="negative_prices",
                initial_soc=4.0,
                import_prices=(-0.08, -0.02, 0.18, 0.26),
                export_prices=(0.02, 0.04, 0.06, 0.05),
                pvs=(0.0, 0.5, 0.0, 0.0),
                loads=(0.6, 0.8, 1.2, 0.9),
            ),
            expected_focus="planner remains offline while negative import prices make charge candidates visible",
            expected_safe=True,
            notes="Grid charge candidates may be evaluated, never executed.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="flat_prices",
            fixture=_fixture(
                name="flat_prices",
                initial_soc=5.0,
                import_prices=(0.20, 0.20, 0.20, 0.20),
                export_prices=(0.08, 0.08, 0.08, 0.08),
                pvs=(0.0, 0.0, 0.0, 0.0),
                loads=(0.0, 0.0, 0.0, 0.0),
                charge_power=0.0,
                discharge_power=0.0,
            ),
            expected_focus="deterministic strategy order tie-breaking",
            expected_safe=True,
            notes="All strategies should tie on cost and select the first strategy.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="full_battery",
            fixture=_fixture(
                name="full_battery",
                initial_soc=10.0,
                import_prices=(0.22, 0.24, 0.28, 0.30),
                export_prices=(0.04, 0.06, 0.08, 0.10),
                pvs=(2.0, 2.5, 1.8, 1.2),
                loads=(0.2, 0.3, 0.4, 0.5),
            ),
            expected_focus="SOC must not exceed maximum and PV surplus/export behavior should be explainable",
            expected_safe=True,
            notes="Full battery clips charge candidates and exports remaining PV.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="empty_battery",
            fixture=_fixture(
                name="empty_battery",
                initial_soc=0.0,
                import_prices=(0.24, 0.26, 0.28, 0.30),
                export_prices=(0.03, 0.04, 0.05, 0.06),
                pvs=(0.0, 0.0, 0.0, 0.0),
                loads=(1.0, 1.2, 0.8, 1.1),
                reserve=0.0,
            ),
            expected_focus="minimum SOC and reserve floors are respected",
            expected_safe=True,
            notes="Load should be imported when the battery has no available energy.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="reserve_reached",
            fixture=_fixture(
                name="reserve_reached",
                initial_soc=2.0,
                reserve=2.0,
                import_prices=(0.30, 0.32, 0.35, 0.33),
                export_prices=(0.12, 0.15, 0.18, 0.14),
                pvs=(0.0, 0.0, 0.0, 0.0),
                loads=(1.0, 1.0, 1.0, 1.0),
            ),
            expected_focus="discharge below reserve must be blocked or clipped",
            expected_safe=True,
            notes="Reserve floor should prevent load service and export discharge.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="high_pv",
            fixture=_fixture(
                name="high_pv",
                initial_soc=3.0,
                import_prices=(0.20, 0.22, 0.24, 0.26),
                export_prices=(0.05, 0.08, 0.10, 0.07),
                pvs=(4.0, 5.0, 3.0, 4.5),
                loads=(0.6, 0.8, 0.7, 0.9),
            ),
            expected_focus="PV surplus, battery charge, and export behavior should be visible",
            expected_safe=True,
            notes="High PV should produce rich slot trace reasons.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="no_pv",
            fixture=_fixture(
                name="no_pv",
                initial_soc=5.0,
                import_prices=(0.21, 0.25, 0.29, 0.31),
                export_prices=(0.04, 0.05, 0.06, 0.07),
                pvs=(0.0, 0.0, 0.0, 0.0),
                loads=(0.8, 1.0, 1.1, 0.9),
            ),
            expected_focus="load import and battery behavior without PV should be visible",
            expected_safe=True,
            notes="No PV removes solar surplus from the trace.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="high_load",
            fixture=_fixture(
                name="high_load",
                initial_soc=6.0,
                import_prices=(0.28, 0.30, 0.34, 0.32),
                export_prices=(0.05, 0.05, 0.06, 0.05),
                pvs=(0.2, 0.1, 0.0, 0.2),
                loads=(4.0, 4.5, 5.0, 4.2),
                discharge_power=1.0,
            ),
            expected_focus="power limits and reserve behavior should be visible under high load",
            expected_safe=True,
            notes="Discharge is power-limited and remaining load is imported.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="export_opportunity",
            fixture=_fixture(
                name="export_opportunity",
                initial_soc=8.0,
                import_prices=(0.12, 0.14, 0.16, 0.18),
                export_prices=(0.10, 0.42, 0.18, 0.12),
                pvs=(0.0, 0.0, 0.0, 0.0),
                loads=(0.2, 0.2, 0.2, 0.2),
            ),
            expected_focus="export-aware candidate path should be evaluated",
            expected_safe=True,
            notes="Highest export slot should produce an export candidate in audit traces.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
        PlannerQualityScenario(
            scenario_name="charge_opportunity",
            fixture=_fixture(
                name="charge_opportunity",
                initial_soc=2.0,
                import_prices=(0.35, 0.04, 0.28, 0.30),
                export_prices=(0.04, 0.04, 0.05, 0.05),
                pvs=(0.0, 0.0, 0.0, 0.0),
                loads=(0.2, 0.2, 0.2, 0.2),
            ),
            expected_focus="cheapest charge candidate path should be evaluated",
            expected_safe=True,
            notes="Lowest import slot should produce a grid charge candidate in audit traces.",
            required_reason_codes=("planner_replay_audit_report",),
        ),
    )


def _fixture(
    *,
    name: str,
    initial_soc: float,
    import_prices: tuple[float, float, float, float],
    export_prices: tuple[float, float, float, float],
    pvs: tuple[float, float, float, float],
    loads: tuple[float, float, float, float],
    reserve: float = 1.0,
    charge_power: float = 2.0,
    discharge_power: float = 2.0,
) -> Mapping[str, Any]:
    return {
        "schema_version": "v2160_planner_quality_scenario",
        "scenario_name": name,
        "observer_only": True,
        "slots": tuple(
            {
                "slot_id": f"{name}_s{slot_index}",
                "pv_kwh": pvs[slot_index],
                "load_kwh": loads[slot_index],
                "import_price_per_kwh": import_prices[slot_index],
                "export_price_per_kwh": export_prices[slot_index],
                "duration_hours": 1.0,
            }
            for slot_index in range(4)
        ),
        "battery": {
            "capacity_kwh": 10.0,
            "min_soc_kwh": 0.0,
            "max_soc_kwh": 10.0,
            "initial_soc_kwh": initial_soc,
            "reserve_kwh": reserve,
            "charge_power_kw": charge_power,
            "discharge_power_kw": discharge_power,
            "round_trip_efficiency": 1.0,
        },
    }


__all__ = [
    "PlannerQualityScenario",
    "REQUIRED_SCENARIO_NAMES",
    "get_planner_quality_scenarios",
]
