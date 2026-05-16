from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON_ROOT))

from app.v1969.tesla_style_cockpit_spec import build_tesla_style_cockpit_spec
from app.v2000.read_only_tesla_cockpit import build_read_only_cockpit_payload, render_tesla_cockpit_html
from energy_brain.web_ui import summarize_cycle


def test_v1969_cockpit_spec_remains_json_serializable():
    spec = build_tesla_style_cockpit_spec()

    json.dumps(spec, sort_keys=True)


def test_cockpit_payload_is_deterministic_display_only():
    summary = summarize_cycle(_cycle())

    first = build_read_only_cockpit_payload(summary)
    second = build_read_only_cockpit_payload(summary)

    assert first == second
    assert first["read_only"] is True
    assert first["observer_only"] is True
    assert first["service_calls_allowed"] is False
    assert first["write_controls_allowed"] is False
    assert first["control_buttons"] == []
    assert first["safety_panel"]["buttons"] == []


def test_cockpit_payload_contains_required_sections():
    payload = build_read_only_cockpit_payload(summarize_cycle(_cycle()))

    for section in [
        "hero_status",
        "read_only_badges",
        "energy_flow",
        "battery_soc_card",
        "soc_trajectory",
        "planner_timeline",
        "price_forecast",
        "pv_forecast",
        "load_forecast",
        "plan_explainability",
        "benchmark_comparison",
        "degraded_mode_banner",
        "safety_panel",
        "latest_cycle_table",
    ]:
        assert section in payload


def test_cockpit_rendered_output_shows_required_sections():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Hero Status",
        "Observer-only/read-only badges",
        "Energy Flow Overview",
        "Battery SOC Card",
        "SOC Trajectory",
        "SOC trajectory placeholder chart area",
        "Planner Timeline",
        "Price Forecast Panel",
        "PV Forecast Panel",
        "Load Forecast Panel",
        "Plan Explainability Panel",
        "Benchmark Comparison Panel",
        "Degraded-Mode Banner",
        "Safety Panel",
        "Latest Cycle Table",
    ]:
        assert label in html


def test_cockpit_empty_state_uses_deterministic_shadow_data():
    payload = build_read_only_cockpit_payload({"status": "safe", "valid_cycle": False, "message": "No valid cycle available"})

    assert payload["degraded_mode_banner"]["active"] is True
    assert payload["degraded_mode_banner"]["fallback_mode"] == "deterministic shadow sample"
    assert payload["latest_cycle_table"] == []
    assert payload["soc_trajectory"]


def test_cockpit_code_has_no_forbidden_runtime_surfaces():
    forbidden = _forbidden_terms()
    files = [
        Path("app/v2000/read_only_tesla_cockpit.py"),
        Path("energy_brain/web_ui.py"),
    ]
    offenders = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        if path == Path("energy_brain/web_ui.py"):
            text = _added_lines(path)
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def test_runtime_controller_files_are_unchanged():
    checks = [
        ["git", "diff", "--", "energy_brain/controller.py", "energy_brain/main.py", "energy_brain/ha_client.py"],
        ["git", "-C", "..", "diff", "--", "app/energy_brain_v5.py"],
    ]

    for command in checks:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        assert result.stdout == ""


def _cycle() -> dict:
    return {
        "mode": "observer",
        "snapshot": {
            "battery_soc_percent": 66.0,
            "pv_power_kw": 3.4,
            "household_load_kw": 1.2,
            "grid_price": 0.29,
        },
        "plan": {
            "valid": True,
            "expected_cost": 1.1,
            "baseline_cost": 1.4,
            "savings_vs_baseline": 0.3,
            "soc_trajectory": [66.0, 67.0, 68.5, 67.5],
            "steps": [
                {"index": 0, "battery_setpoint_kw": 0.0, "soc_percent": 66.0, "reason": "hold"},
                {"index": 1, "battery_setpoint_kw": 1.4, "soc_percent": 67.0, "reason": "charge_from_pv_surplus"},
                {"index": 2, "battery_setpoint_kw": 0.0, "soc_percent": 68.5, "reason": "reserve_hold"},
                {"index": 3, "battery_setpoint_kw": -0.7, "soc_percent": 67.5, "reason": "discharge_to_load"},
            ],
        },
        "controller": {
            "approved": True,
            "execute": False,
            "setpoint_kw": 0.0,
        },
        "execution": {
            "attempted": False,
        },
    }


def _added_lines(path: Path) -> str:
    result = subprocess.run(["git", "diff", "-U0", "--", str(path)], check=True, capture_output=True, text=True)
    lines = []
    for line in result.stdout.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return "\n".join(lines)


def _forbidden_terms() -> list[str]:
    pieces = [
        ("call", "_", "service", "("),
        ("hass", ".", "services"),
        ("set", "_", "state", "("),
        ("input", "_", "boolean", "."),
        ("input", "_", "number", "."),
        ("input", "_", "select", "."),
        ("switch", "."),
        ("climate", "."),
        ("notify", "."),
        ("shell", "_", "command", "."),
        ("dis", "patch"),
        ("execute",),
        ("requests",),
        ("aio", "http"),
        ("url", "lib"),
    ]
    return ["".join(piece) for piece in pieces]
