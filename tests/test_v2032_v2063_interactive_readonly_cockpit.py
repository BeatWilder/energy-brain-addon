from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path

from energy_brain.v2000.read_only_tesla_cockpit import build_read_only_cockpit_payload, render_tesla_cockpit_html
from energy_brain.web_ui import summarize_cycle


ADDON_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON_ROOT))


def test_interactive_cockpit_renders_required_tabs_and_safety_rail():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in ["Overview", "Plan", "Forecast", "Benchmark", "Safety"]:
        assert f">{label}<" in html

    for badge in ["OBSERVER-ONLY", "READ-ONLY", "NO DISPATCH", "NO SERVICE CALLS", "DISPLAY ONLY"]:
        assert badge in html
    assert 'aria-label="Safety rail visible on every tab"' in html


def test_plan_timeline_has_clickable_inspect_steps_and_detail_panel():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle(step_count=30)))

    assert html.count('class="step-button') >= 24
    assert "Selected-Step Inspector" in html
    assert 'id="selected-step-inspector"' in html
    for label in [
        "step index",
        "SOC %",
        "battery setpoint kW",
        "reason code",
        "price",
        "PV forecast",
        "load forecast",
        "grid estimate",
        "validation/display-only status",
    ]:
        assert label in html


def test_plan_windows_horizon_chart_and_explainability_are_rendered():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Predbat-Inspired Plan Windows",
        "charge windows",
        "hold windows",
        "clamp/max-SOC windows",
        "baseline comparison windows",
        "Integrated Horizon Chart",
        "SOC line",
        "price bars",
        "PV/load overlays",
        "reserve band",
        "Reason-Code Summary",
        "Selected Reason-Code Explanation",
        "Constraints Applied",
        "Degraded-Mode Explanation",
    ]:
        assert label in html
    assert 'id="reason-code-explanation-area"' in html


def test_benchmark_notice_and_json_viewer_toggle_are_rendered():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    assert "Energy Brain expected cost" in html
    assert "baseline cost" in html
    assert "delta" in html
    assert "Predbat is benchmark/reference only, not runtime dependency" in html
    assert "Show read-only JSON viewer" in html
    assert 'aria-label="Read-only current /api/tesla-cockpit payload"' in html


def test_payload_is_json_serializable_and_display_only():
    payload = build_read_only_cockpit_payload(summarize_cycle(_cycle()))

    json.dumps(payload, sort_keys=True)
    assert payload["read_only"] is True
    assert payload["observer_only"] is True
    assert payload["service_calls_allowed"] is False
    assert payload["write_controls_allowed"] is False
    assert payload["control_buttons"] == []
    assert payload["safety_panel"]["buttons"] == []
    assert len(payload["planner_timeline"]) == 24


def test_ui_contains_no_dispatch_or_write_control_markup():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    disallowed_markup = ["<form", 'type="submit"', "data-control", "service-call", "write-control"]
    assert [item for item in disallowed_markup if item in html.lower()] == []
    assert "inspect only" in html


def test_forbidden_runtime_surfaces_are_absent_from_changed_new_files():
    offenders: list[str] = []
    files = [
        Path("energy_brain/v2000/read_only_tesla_cockpit.py"),
        Path("energy_brain/web_ui.py"),
        Path("tests/test_v2032_v2063_interactive_readonly_cockpit.py"),
        Path("tools/run_v2032_v2063_interactive_readonly_cockpit_smoke.sh"),
    ]

    for path in files:
        if not path.exists():
            continue
        text = _scan_text(path)
        offenders.extend(f"{path}:{term}" for term in _forbidden_terms() if term in text)

    assert offenders == []


def test_no_non_get_handler_methods_exist_on_web_ui_handler():
    import energy_brain.web_ui as web_ui

    handler_names = set(dir(web_ui.EnergyBrainWebUIHandler))
    blocked = [_join("do", "_", method) for method in ["POST", "PUT", "PATCH", "DELETE"]]

    assert [name for name in blocked if name in handler_names] == []


def test_required_modules_import_successfully():
    for module_name in [
        "energy_brain.web_ui",
        "energy_brain.v2000.read_only_tesla_cockpit",
        "app.v2000.read_only_tesla_cockpit",
    ]:
        importlib.import_module(module_name)


def test_app_v1969_remains_standard_library_only():
    path = Path("app/v1969/tesla_style_cockpit_spec.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])

    assert set(imports) <= {"__future__", "typing"}


def test_protected_runtime_controller_files_are_unchanged():
    result = subprocess.run(
        ["git", "diff", "--", "energy_brain/controller.py", "energy_brain/main.py", "energy_brain/ha_client.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""


def _cycle(*, step_count: int = 24) -> dict:
    reasons = [
        "hold",
        "charge_from_pv_surplus",
        "reserve_hold",
        "max_soc_clamp",
        "baseline_compare",
        "discharge_to_load",
    ]
    steps = []
    for index in range(step_count):
        setpoint = 1.2 if index in (1, 2, 9, 10) else (-0.6 if index in (18, 19) else 0.0)
        steps.append(
            {
                "index": index,
                "battery_setpoint_kw": setpoint,
                "soc_percent": round(63.0 + index * 0.35 - max(0, index - 14) * 0.42, 2),
                "reason": reasons[index % len(reasons)],
                "price": round(0.28 + (index % 5) * 0.013, 3),
                "pv_forecast": round(max(0.0, 2.4 + (index % 7) * 0.2), 2),
                "load_forecast": round(1.1 + (index % 4) * 0.18, 2),
                "grid_estimate": round(1.1 - 2.4 - setpoint, 2),
            }
        )

    return {
        "mode": "observer",
        "snapshot": {
            "battery_soc_percent": 63.0,
            "pv_power_kw": 2.4,
            "household_load_kw": 1.1,
            "grid_price": 0.28,
        },
        "plan": {
            "valid": True,
            "expected_cost": 1.08,
            "baseline_cost": 1.42,
            "savings_vs_baseline": 0.34,
            "soc_trajectory": [step["soc_percent"] for step in steps],
            "steps": steps,
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


def _scan_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path == Path("energy_brain/web_ui.py"):
        result = subprocess.run(["git", "diff", "-U0", "--", str(path)], check=True, capture_output=True, text=True)
        return "\n".join(line[1:] for line in result.stdout.splitlines() if line.startswith("+") and not line.startswith("+++"))
    if path.name.endswith("_smoke.sh"):
        return "\n".join(line for line in text.splitlines() if "printf" not in line)
    return text


def _forbidden_terms() -> list[str]:
    parts = [
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
        ("do", "_", "POST"),
        ("do", "_", "PUT"),
        ("do", "_", "PATCH"),
        ("do", "_", "DELETE"),
        ("dis", "patch", "("),
        ("execute", "("),
        ("write", "_", "service"),
        ("control", "_", "service"),
    ]
    return [_join(*part) for part in parts]


def _join(*parts: str) -> str:
    return "".join(parts)
