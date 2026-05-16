"""Clean-room Predbat UX reverse-spec for Energy Brain.

This module is specification data only. It has no runtime integration with
Home Assistant, AppDaemon, Predbat, GitHub, or live devices.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v2256_v2287.predbat_ux_reverse_spec.no_code_copy.1"


def clean_room_boundaries() -> dict[str, Any]:
    return {
        "no_predbat_source_copied": True,
        "no_predbat_imports": True,
        "no_predbat_runtime_dependency": True,
        "no_runtime_github_or_docs_scraping": True,
        "no_predbat_assets_screens_css_html_copied": True,
        "home_assistant_write_allowed": False,
        "service_calls_allowed": False,
        "dispatch_allowed": False,
        "controller_changes_allowed": False,
        "runtime_network_access_allowed": False,
        "predbat_import_allowed": False,
        "notes": [
            "Predbat is studied manually as benchmark/reference only.",
            "Energy Brain remains independent and read-only in this specification.",
            "No controller, adapter, or device-control behavior is introduced.",
        ],
    }


def predbat_ux_lessons() -> list[dict[str, str]]:
    return [
        {
            "id": "battery_prediction_over_time",
            "title": "Battery prediction over time",
            "lesson": "A household user needs to see expected battery filling over the day, not only current values.",
        },
        {
            "id": "plan_card_and_windows",
            "title": "Plan card / plan windows",
            "lesson": "Planner windows become useful when they are summarized as readable periods with intent.",
        },
        {
            "id": "charge_hold_export_windows",
            "title": "Charge / hold / export windows",
            "lesson": "Windows should be labelled as household actions such as charging, holding, or export consideration.",
        },
        {
            "id": "cost_comparison",
            "title": "Cost comparison",
            "lesson": "A plan should be compared with a simple baseline and should state whether the difference is reliable.",
        },
        {
            "id": "actual_vs_predicted",
            "title": "Actual vs predicted",
            "lesson": "A cockpit should help users see whether forecasts match reality before trusting automation.",
        },
        {
            "id": "scenario_thinking",
            "title": "Scenario thinking",
            "lesson": "Normal, lower-solar, and higher-use cases make forecast uncertainty understandable.",
        },
        {
            "id": "read_only_planning",
            "title": "Read-only planning",
            "lesson": "Planning can be valuable as observer/shadow output without sending instructions to devices.",
        },
        {
            "id": "debug_advanced_details",
            "title": "Debug/advanced details",
            "lesson": "Raw details are useful for diagnosis but should be hidden behind an advanced layer by default.",
        },
        {
            "id": "warnings_degraded_states",
            "title": "Warnings/degraded states",
            "lesson": "Missing, stale, or untrusted inputs should be visible as plain-language warnings.",
        },
        {
            "id": "explainability",
            "title": "Explainability",
            "lesson": "Every selected period should explain what happens, why, and what it means for the home.",
        },
    ]


def energy_brain_adaptations() -> list[dict[str, str]]:
    return [
        {
            "id": "layperson_summary",
            "title": "Kort gezegd",
            "requirement": "Start with one sentence that says Energy Brain is observing and what the next logical step appears to be.",
        },
        {
            "id": "nu_in_huis",
            "title": "Nu in huis",
            "requirement": "Translate battery, solar, household use, and grid balance into household language.",
        },
        {
            "id": "simple_dayline",
            "title": "Simpele daglijn",
            "requirement": "Show Nu, Straks, Vanavond, and Morgen before any technical timeline.",
        },
        {
            "id": "plain_plan",
            "title": "Plan in gewone taal",
            "requirement": "Use labels such as Laden met zon, Vasthouden, and Bijna vol, laden begrensd.",
        },
        {
            "id": "cost_confidence",
            "title": "Kostenvergelijking",
            "requirement": "Show baseline difference with confidence text when data is incomplete.",
        },
        {
            "id": "scenario_cards",
            "title": "Scenario's",
            "requirement": "Show Normal, Minder zon, and Meer verbruik as read-only planning examples.",
        },
        {
            "id": "actual_prediction",
            "title": "Voorspelling vs werkelijkheid",
            "requirement": "Only claim forecast quality when enough measurement history exists.",
        },
        {
            "id": "safety",
            "title": "Veiligheid",
            "requirement": "Always state that the cockpit is read-only and changes nothing.",
        },
        {
            "id": "technical_details_hidden",
            "title": "Technische details",
            "requirement": "Keep reason codes and raw planner data available but hidden by default.",
        },
    ]


def energy_brain_rejections() -> list[dict[str, str]]:
    return [
        {
            "id": "source_copying",
            "title": "Source copying",
            "reason": "Energy Brain must be clean-room and use only its own implementation.",
        },
        {
            "id": "runtime_dependency",
            "title": "Runtime dependency",
            "reason": "Predbat remains a benchmark/reference, not a package Energy Brain loads.",
        },
        {
            "id": "service_calls",
            "title": "Planner service calls",
            "reason": "A cockpit or planner view must not call Home Assistant services.",
        },
        {
            "id": "controller_changes",
            "title": "Controller changes",
            "reason": "This sprint is documentation/specification only; protected controller files stay unchanged.",
        },
        {
            "id": "direct_device_control",
            "title": "Direct device control",
            "reason": "The cockpit must never be a direct inverter or battery control surface.",
        },
        {
            "id": "monolithic_runtime_shape",
            "title": "Monolithic runtime shape",
            "reason": "Energy Brain keeps data, forecast, planner, policy, controller, and device boundaries separate.",
        },
        {
            "id": "raw_reason_first_ui",
            "title": "Raw reason-code-first UI",
            "reason": "Normal users need a plain explanation before raw codes.",
        },
    ]


def future_backlog() -> list[dict[str, str]]:
    return [
        {
            "version": "V2288-V2319",
            "title": "Predbat-style Energy Brain plan card",
            "outcome": "Energy Brain-owned plan card with dayline, windows, and plain household labels.",
        },
        {
            "version": "V2320-V2351",
            "title": "actual-vs-predicted read-only comparison",
            "outcome": "Compare forecast and observed values without adding any control path.",
        },
        {
            "version": "V2352-V2383",
            "title": "scenario cards normal/minder zon/meer verbruik",
            "outcome": "Show deterministic scenario cards using existing planner data or clear fallback labels.",
        },
        {
            "version": "V2384-V2415",
            "title": "cost comparison confidence labels",
            "outcome": "Mark cost deltas as reliable, uncertain, or shadow-only.",
        },
        {
            "version": "V2416-V2447",
            "title": "technical graph as collapsible debug view",
            "outcome": "Move technical graph detail behind a collapsed inspect section by default.",
        },
        {
            "version": "V2448-V2479",
            "title": "live snapshot data quality panel",
            "outcome": "Show freshness and reliability for solar, load, price, and battery data.",
        },
    ]


def build_predbat_ux_reverse_spec() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_role": "benchmark_reference_only",
        "no_code_copy": True,
        "runtime_dependency_allowed": False,
        "home_assistant_write_allowed": False,
        "service_calls_allowed": False,
        "dispatch_allowed": False,
        "controller_changes_allowed": False,
        "runtime_network_access_allowed": False,
        "predbat_import_allowed": False,
        "ui_mode": "read_only_reverse_spec",
        "clean_room_status": "enforced",
        "clean_room_boundaries": clean_room_boundaries(),
        "predbat_ux_lessons": predbat_ux_lessons(),
        "energy_brain_adaptations": energy_brain_adaptations(),
        "energy_brain_rejections": energy_brain_rejections(),
        "future_backlog": future_backlog(),
        "acceptance_criteria": [
            "Future implementation remains read-only unless separately approved.",
            "Protected controller files remain unchanged.",
            "Smoke tests pass before release.",
            "No forbidden runtime surfaces are introduced.",
            "The cockpit remains explainable to a layperson.",
        ],
    }


def validate_reverse_spec_safety(spec: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    false_flags = [
        "runtime_dependency_allowed",
        "home_assistant_write_allowed",
        "service_calls_allowed",
        "dispatch_allowed",
        "controller_changes_allowed",
        "runtime_network_access_allowed",
        "predbat_import_allowed",
    ]
    true_flags = ["no_code_copy"]

    if spec.get("source_role") != "benchmark_reference_only":
        errors.append("source_role_not_benchmark_reference_only")
    if spec.get("ui_mode") != "read_only_reverse_spec":
        errors.append("ui_mode_not_read_only_reverse_spec")
    if spec.get("clean_room_status") != "enforced":
        errors.append("clean_room_status_not_enforced")
    for flag in false_flags:
        if spec.get(flag) is not False:
            errors.append(f"{flag}_not_false")
    for flag in true_flags:
        if spec.get(flag) is not True:
            errors.append(f"{flag}_not_true")

    boundary = spec.get("clean_room_boundaries", {})
    if not isinstance(boundary, dict):
        errors.append("clean_room_boundaries_missing")
    else:
        for flag in ("no_predbat_source_copied", "no_predbat_imports", "no_predbat_runtime_dependency"):
            if boundary.get(flag) is not True:
                errors.append(f"{flag}_not_true")

    if len(spec.get("future_backlog", [])) < 6:
        errors.append("future_backlog_too_short")

    return {
        "schema_version": "v2256_v2287.predbat_ux_reverse_spec.validation.1",
        "valid": not errors,
        "errors": errors,
        "checked_false_flags": false_flags,
        "checked_true_flags": true_flags,
    }


def write_reverse_spec_report(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    spec = build_predbat_ux_reverse_spec()
    target.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "schema_version": "v2256_v2287.predbat_ux_reverse_spec.report_write.1",
        "path": str(target),
        "bytes": target.stat().st_size,
        "written": True,
    }
