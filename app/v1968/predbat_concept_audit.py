"""Offline Predbat concept audit for Energy Brain planning research.

This module treats Predbat as a benchmark reference only. It is deliberately
standard-library only, deterministic, and safe to import in environments where
Home Assistant, AppDaemon, and Predbat are not installed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v1968.predbat_concept_audit.1"
SOURCE_ROLE = "benchmark_reference_only"


def classify_predbat_lessons() -> dict[str, list[dict[str, str]]]:
    """Classify concept-level Predbat lessons for Energy Brain."""

    return {
        "adopt_as_principle": [
            {
                "lesson": "normalize_forecasts_before_planning",
                "rationale": (
                    "Planner inputs should be converted into aligned time slots "
                    "with explicit units, confidence notes, and missing-data flags."
                ),
            },
            {
                "lesson": "forward_soc_simulation",
                "rationale": (
                    "A visible forward SOC trajectory makes plans easier to test, "
                    "compare, and explain before any controller observes them."
                ),
            },
            {
                "lesson": "explainable_reason_codes",
                "rationale": (
                    "Each planning interval should expose why it is holding, "
                    "charging, preserving reserve, or rejecting a candidate."
                ),
            },
            {
                "lesson": "read_only_first_operation",
                "rationale": (
                    "Observer and shadow outputs are the correct default for "
                    "auditing planner quality without changing devices."
                ),
            },
        ],
        "adapt_to_energy_brain": [
            {
                "lesson": "candidate_charge_discharge_export_windows",
                "rationale": (
                    "Window candidates are useful as planner hypotheses, but must "
                    "remain detached from Home Assistant writes and device control."
                ),
            },
            {
                "lesson": "reserve_handling",
                "rationale": (
                    "Reserve should be modeled in the planner and independently "
                    "enforced by controller safety checks with clear degradation."
                ),
            },
            {
                "lesson": "anti_churn_plan_acceptance",
                "rationale": (
                    "Energy Brain can compare current and proposed plans with "
                    "hysteresis, age, confidence, and benefit thresholds."
                ),
            },
            {
                "lesson": "benchmark_comparison",
                "rationale": (
                    "Predbat-inspired baseline comparisons should be reports, not "
                    "execution paths, so planner regressions are visible offline."
                ),
            },
        ],
        "reject_for_energy_brain": [
            {
                "lesson": "mixed_planner_and_device_execution",
                "rationale": (
                    "Energy Brain must keep planner, policy, controller, and device "
                    "adapter boundaries explicit and separately testable."
                ),
            },
            {
                "lesson": "runtime_dependency_on_predbat",
                "rationale": (
                    "Predbat is a reference target only; Energy Brain must not import "
                    "it, vendor it, or depend on its runtime behavior."
                ),
            },
            {
                "lesson": "ui_controls_that_change_live_execution",
                "rationale": (
                    "The future cockpit should show observer, shadow, comparison, "
                    "and safety state only, with no direct execution controls."
                ),
            },
        ],
        "future_research": [
            {
                "lesson": "multi_forecast_confidence_scoring",
                "rationale": (
                    "Compare solar, load, tariff, and actual history quality before "
                    "allowing a planner candidate to supersede a stable plan."
                ),
            },
            {
                "lesson": "degraded_mode_explainability",
                "rationale": (
                    "Expose which inputs are stale or missing and show the exact "
                    "reason a cycle stayed observer-only."
                ),
            },
            {
                "lesson": "offline_shadow_leaderboard",
                "rationale": (
                    "Evaluate Energy Brain plans against baseline heuristics and "
                    "Predbat-inspired concepts without adding runtime coupling."
                ),
            },
        ],
    }


def build_predbat_concept_audit() -> dict[str, Any]:
    """Build a deterministic read-only audit dictionary."""

    lessons = classify_predbat_lessons()
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "title": "V1968-V1999 Predbat-inspired planner benchmark audit",
        "source_role": SOURCE_ROLE,
        "safety_boundary": {
            "status": "sealed_observer_only_reference",
            "runtime_dependency_allowed": False,
            "home_assistant_write_allowed": False,
            "controller_execution_allowed": False,
            "planner_dispatch_allowed": False,
            "ui_dispatch_allowed": False,
            "observer_only": True,
            "copied_source_code": False,
            "runtime_network_access": False,
        },
        "concept_scope": {
            "forecast_normalization": (
                "Normalize PV, load, tariff, reserve, and current-state inputs "
                "into aligned planning intervals with explicit gaps."
            ),
            "forward_soc_simulation": (
                "Simulate SOC forward under each candidate plan and retain the "
                "trajectory for comparison and explanation."
            ),
            "candidate_windows": (
                "Represent charge, discharge, export, and hold periods as planner "
                "candidates only; never as device instructions."
            ),
            "reserve_handling": (
                "Treat reserve as a hard safety boundary and annotate intervals "
                "where reserve limits constrain planner choices."
            ),
            "read_only_degraded_modes": (
                "Fail closed to observer-only when inputs are missing, stale, or "
                "insufficiently trusted."
            ),
            "anti_churn_plan_acceptance": (
                "Require material benefit and stable inputs before replacing a "
                "previous shadow plan."
            ),
            "explainability": (
                "Emit compact reason codes and human-readable rationale for each "
                "planner interval and rejected candidate."
            ),
        },
        "lesson_classification": lessons,
        "energy_brain_position": {
            "benchmark_reference": (
                "Predbat is useful as a planning-quality and UI reference, not as "
                "an architecture to clone or a runtime component."
            ),
            "stricter_boundaries": (
                "Energy Brain should keep forecasting, planning, policy, controller, "
                "device adapters, Home Assistant adapters, logging, and tests split."
            ),
            "observer_ui_path": (
                "The concepts can later feed a read-only cockpit that displays "
                "shadow plans, safety flags, degraded state, and benchmark deltas."
            ),
        },
        "reference_notes": [
            {
                "name": "Predbat documentation",
                "role": "conceptual planning and UI benchmark",
                "runtime_use": "none",
            },
            {
                "name": "Predbat GitHub repository",
                "role": "human research reference",
                "runtime_use": "none",
            },
        ],
    }
    return audit


def validate_predbat_audit_safety(audit: dict[str, Any]) -> dict[str, Any]:
    """Validate that an audit dictionary remains sealed and observer-only."""

    boundary = audit.get("safety_boundary", {})
    required_false = {
        "runtime_dependency_allowed",
        "home_assistant_write_allowed",
        "controller_execution_allowed",
        "planner_dispatch_allowed",
        "ui_dispatch_allowed",
        "copied_source_code",
        "runtime_network_access",
    }
    errors: list[str] = []

    if audit.get("source_role") != SOURCE_ROLE:
        errors.append("source_role_not_benchmark_reference_only")
    if boundary.get("observer_only") is not True:
        errors.append("observer_only_not_true")
    for flag in sorted(required_false):
        if boundary.get(flag) is not False:
            errors.append(f"{flag}_not_false")

    categories = audit.get("lesson_classification", {})
    expected_categories = {
        "adopt_as_principle",
        "adapt_to_energy_brain",
        "reject_for_energy_brain",
        "future_research",
    }
    missing = sorted(expected_categories.difference(categories))
    for category in missing:
        errors.append(f"missing_category:{category}")

    return {
        "schema_version": "v1968.predbat_concept_audit.validation.1",
        "valid": not errors,
        "errors": errors,
        "observer_only": boundary.get("observer_only") is True,
        "checked_false_flags": sorted(required_false),
    }


def write_audit_report(path: str | Path) -> dict[str, Any]:
    """Write the audit as JSON only when the caller explicitly provides a path."""

    report_path = Path(path)
    audit = build_predbat_concept_audit()
    validation = validate_predbat_audit_safety(audit)
    payload = {
        "audit": audit,
        "validation": validation,
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema_version": "v1968.predbat_concept_audit.report.1",
        "written": True,
        "path": str(report_path),
        "validation": validation,
    }

