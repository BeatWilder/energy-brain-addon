from __future__ import annotations

import subprocess
from pathlib import Path

from energy_brain.v2000.read_only_tesla_cockpit import render_tesla_cockpit_html
from energy_brain.web_ui import summarize_cycle


def test_chart_has_readable_title_legend_axes_and_how_to_read_text():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "SOC Trajectory",
        "SOC trajectory",
        "Reserve / min SOC",
        "Max SOC",
        "Price",
        "PV/load overlay",
        "SOC %",
        "step / hour",
        "How to read this chart",
    ]:
        assert label in html


def test_chart_decision_segments_and_selected_marker_are_visible():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "charge_from_pv_surplus",
        "max_soc_clamped_charge",
        "max_soc_hold",
        "reserve band",
        'id="selected-step-marker"',
        "Current/selected step details",
    ]:
        assert label in html


def test_clickable_tabs_and_step_selection_markup_are_present():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in ["Overview", "Plan", "Forecast", "Benchmark", "Safety"]:
        assert f">{label}<" in html

    for panel_id in ["overview", "plan", "forecast", "benchmark", "safety"]:
        assert f'data-tab-panel="{panel_id}"' in html

    assert "addEventListener('click'" in html
    assert "showStep(" in html
    assert "dataset.tab" in html
    assert "dataset.step" in html
    assert 'data-step="0"' in html
    assert "Klik op een stap om details te bekijken" in html


def test_selected_step_detail_panel_is_clear_and_read_only():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Selected-Step Inspector",
        'id="step-detail-panel"',
        "selected step index/time",
        "SOC %",
        "battery setpoint kW",
        "reason code",
        "price",
        "PV forecast",
        "load forecast",
        "safety status",
        "no dispatch",
        "constraint applied",
        'id="selected-reason-explanation"',
    ]:
        assert label in html


def test_predbat_explanation_and_degraded_state_are_explicit():
    html = render_tesla_cockpit_html({"status": "safe", "valid_cycle": False, "message": "No valid cycle available"})

    for label in [
        "Predbat is benchmark/reference only",
        "These windows are conceptual comparison labels",
        "Energy Brain does not depend on Predbat at runtime",
        "No commands are sent from this cockpit",
        "Degraded-Mode Banner",
        "display fallback values",
        "missing source",
        "deterministic shadow sample",
    ]:
        assert label in html


def test_json_viewer_remains_read_only_and_no_non_get_handlers_exist():
    import energy_brain.web_ui as web_ui

    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))
    blocked = [_join("do", "_", method) for method in ["POST", "PUT", "PATCH", "DELETE"]]

    assert "Show read-only JSON viewer" in html
    assert 'aria-label="Read-only current /api/tesla-cockpit payload"' in html
    assert [name for name in blocked if hasattr(web_ui.EnergyBrainWebUIHandler, name)] == []


def test_changed_new_files_have_no_write_or_control_terms():
    offenders: list[str] = []
    for path in [
        Path("energy_brain/v2000/read_only_tesla_cockpit.py"),
        Path("energy_brain/web_ui.py"),
        Path("tests/test_v2064_v2095_usable_interactive_cockpit.py"),
        Path("tools/run_v2064_v2095_usable_interactive_cockpit_smoke.sh"),
    ]:
        if not path.exists():
            continue
        text = _scan_text(path)
        offenders.extend(f"{path}:{term}" for term in _forbidden_terms() if term in text)

    assert offenders == []


def test_protected_files_are_unchanged():
    result = subprocess.run(
        ["git", "diff", "--", "energy_brain/controller.py", "energy_brain/main.py", "energy_brain/ha_client.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""


def _cycle() -> dict:
    reasons = [
        "hold",
        "charge_from_pv_surplus",
        "max_soc_clamped_charge",
        "max_soc_hold",
        "reserve_hold",
        "baseline_compare",
    ]
    steps = []
    for index in range(24):
        setpoint = 1.1 if index in (1, 2, 8) else 0.0
        steps.append(
            {
                "index": index,
                "battery_setpoint_kw": setpoint,
                "soc_percent": round(62.0 + min(index, 10) * 0.7 - max(0, index - 12) * 0.25, 2),
                "reason": reasons[index % len(reasons)],
                "price": round(0.25 + (index % 6) * 0.014, 3),
                "pv_forecast": round(1.8 + (index % 8) * 0.24, 2),
                "load_forecast": round(1.0 + (index % 5) * 0.12, 2),
            }
        )
    return {
        "mode": "observer",
        "snapshot": {
            "battery_soc_percent": 62.0,
            "pv_power_kw": 2.1,
            "household_load_kw": 1.0,
            "grid_price": 0.25,
        },
        "plan": {
            "valid": True,
            "expected_cost": 0.98,
            "baseline_cost": 1.31,
            "savings_vs_baseline": 0.33,
            "soc_trajectory": [step["soc_percent"] for step in steps],
            "steps": steps,
        },
        "controller": {"approved": True, "execute": False, "setpoint_kw": 0.0},
        "execution": {"attempted": False},
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
        ("ap", "ply"),
        ("sa", "ve"),
        ("enable", " ", "control"),
        ("start", " ", "control"),
    ]
    return [_join(*part) for part in parts]


def _join(*parts: str) -> str:
    return "".join(parts)
