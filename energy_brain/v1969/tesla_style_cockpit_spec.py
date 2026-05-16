"""Read-only Tesla-style EMS cockpit specification.

The specification is data only. It does not render a UI, open sockets, read Home
Assistant state, or provide controls that can change live execution.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "v1969.tesla_style_cockpit_spec.1"

REQUIRED_SECTIONS = (
    "hero_status",
    "energy_flow",
    "battery_soc_card",
    "planner_timeline",
    "soc_trajectory",
    "price_forecast",
    "pv_forecast",
    "load_forecast",
    "plan_explainability",
    "benchmark_comparison",
    "degraded_mode_banner",
    "read_only_badges",
    "safety_panel",
    "latest_cycle_table",
)


def build_tesla_style_cockpit_spec() -> dict[str, Any]:
    """Return a deterministic read-only cockpit design specification."""

    sections = {
        "hero_status": {
            "purpose": "Show observer-only operating state, latest cycle time, and planner confidence.",
            "data": ["mode", "cycle_age", "planner_validity", "degraded_state"],
            "controls": [],
        },
        "energy_flow": {
            "purpose": "Display PV, battery, house load, and grid flow as read-only telemetry.",
            "data": ["pv_kw", "battery_kw", "load_kw", "grid_kw"],
            "controls": [],
        },
        "battery_soc_card": {
            "purpose": "Emphasize current SOC, reserve floor, forecast minimum, and forecast maximum.",
            "data": ["soc_percent", "reserve_percent", "min_forecast_soc", "max_forecast_soc"],
            "controls": [],
        },
        "planner_timeline": {
            "purpose": "Show charge, hold, discharge, reserve, and rejected candidate intervals.",
            "data": ["interval", "planned_state", "reason_code", "candidate_delta"],
            "controls": [],
        },
        "soc_trajectory": {
            "purpose": "Make the forward SOC simulation the central planning artifact.",
            "data": ["time", "soc_percent", "reserve_floor", "confidence_band"],
            "controls": [],
        },
        "price_forecast": {
            "purpose": "Display import and export price intervals used by the offline planner.",
            "data": ["time", "import_price", "export_price", "source_quality"],
            "controls": [],
        },
        "pv_forecast": {
            "purpose": "Display normalized PV forecast and uncertainty indicators.",
            "data": ["time", "pv_kwh", "forecast_source", "staleness"],
            "controls": [],
        },
        "load_forecast": {
            "purpose": "Display load forecast, recent baseline, and anomaly markers.",
            "data": ["time", "load_kwh", "baseline_kwh", "confidence"],
            "controls": [],
        },
        "plan_explainability": {
            "purpose": "Expose reason codes, rejected alternatives, and safety constraints.",
            "data": ["reason_code", "summary", "constraint", "interval_count"],
            "controls": [],
        },
        "benchmark_comparison": {
            "purpose": "Compare Energy Brain shadow plans with baseline and Predbat-inspired concepts.",
            "data": ["baseline_cost", "shadow_cost", "delta", "quality_notes"],
            "controls": [],
        },
        "degraded_mode_banner": {
            "purpose": "Keep missing, stale, or untrusted inputs visible at the top of the cockpit.",
            "data": ["degraded_reason", "affected_layer", "fallback_mode"],
            "controls": [],
        },
        "read_only_badges": {
            "purpose": "Keep observer-only, read-only, no-dispatch, and no-service-call status visible.",
            "data": ["observer_only", "read_only", "no_dispatch", "no_service_calls"],
            "controls": [],
        },
        "safety_panel": {
            "purpose": "Show disabled execution/write permissions and protected boundary state.",
            "data": ["execution_flags", "write_flags", "controller_boundary", "adapter_boundary"],
            "controls": [],
        },
        "latest_cycle_table": {
            "purpose": "Display the latest observer/shadow cycle rows for audit and debugging.",
            "data": ["step", "soc_percent", "setpoint_kw", "reason_code", "validity"],
            "controls": [],
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "ui_mode": "read_only_cockpit_spec",
        "observer_only": True,
        "dispatch_controls_allowed": False,
        "service_calls_allowed": False,
        "write_controls_allowed": False,
        "safety_badges": ["observer_only", "read_only", "no_dispatch", "no_service_calls"],
        "design_tokens": {
            "theme": "calm_dark_tesla_style",
            "font_stack": "system",
            "background": "#05070a",
            "surface": "#111820",
            "surface_subtle": "#17212b",
            "text_primary": "#eef4f8",
            "text_secondary": "#a8b5c0",
            "accent_energy": "#3fd5a5",
            "accent_warning": "#f2b84b",
            "accent_grid": "#6aa7ff",
            "accent_pv": "#ffd166",
            "border": "#273441",
            "radius_px": 8,
            "density": "readable_cards",
            "layout": {
                "max_width_px": 1440,
                "grid_gap_px": 16,
                "mobile_breakpoint_px": 760,
                "soc_trajectory_priority": "primary",
            },
        },
        "sections": sections,
        "read_only_rules": [
            "display observer, shadow, comparison, and degraded-mode data only",
            "do not include live execution toggles",
            "do not include helper write controls",
            "do not include direct action controls",
            "keep observer-only status always visible",
        ],
    }


def validate_cockpit_spec_safety(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate that a cockpit specification is display-only."""

    errors: list[str] = []
    if spec.get("ui_mode") != "read_only_cockpit_spec":
        errors.append("ui_mode_not_read_only_cockpit_spec")
    if spec.get("observer_only") is not True:
        errors.append("observer_only_not_true")

    false_flags = (
        "dispatch_controls_allowed",
        "service_calls_allowed",
        "write_controls_allowed",
    )
    for flag in false_flags:
        if spec.get(flag) is not False:
            errors.append(f"{flag}_not_false")

    sections = spec.get("sections", {})
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"missing_section:{section}")
            continue
        if sections[section].get("controls") != []:
            errors.append(f"section_controls_not_empty:{section}")

    badges = set(spec.get("safety_badges", []))
    for badge in ("observer_only", "read_only", "no_dispatch", "no_service_calls"):
        if badge not in badges:
            errors.append(f"missing_badge:{badge}")

    return {
        "schema_version": "v1969.tesla_style_cockpit_spec.validation.1",
        "valid": not errors,
        "errors": errors,
        "observer_only": spec.get("observer_only") is True,
        "checked_sections": list(REQUIRED_SECTIONS),
    }

