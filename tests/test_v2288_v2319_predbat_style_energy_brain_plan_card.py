from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from energy_brain.v2000.read_only_tesla_cockpit import (
    build_read_only_cockpit_payload,
    plan_card_sections,
    plan_confidence,
    render_tesla_cockpit_html,
    today_summary,
)
from energy_brain.web_ui import summarize_cycle


def test_overview_leads_with_plain_plan_card_and_summary():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Planning in gewone taal",
        "Vandaag samengevat",
        "Nu",
        "Straks",
        "Vanavond",
        "Morgen",
        "Alleen meekijken",
        "Technische grafiek voor controle",
        "Niet nodig voor dagelijks gebruik",
    ]:
        assert label in html

    assert html.index("Planning in gewone taal") < html.index("Technische grafiek voor controle")


def test_overview_no_longer_promotes_technical_graph_terms():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))
    overview = html.split('<section id="tab-plan"', 1)[0]

    assert "SOC Trajectory" not in overview
    assert "Decision bands" not in overview


def test_plan_card_sections_are_deterministic_four_part_dayline():
    payload = build_read_only_cockpit_payload(summarize_cycle(_cycle()))
    first = plan_card_sections(payload)
    second = plan_card_sections(payload)

    assert first == second
    assert [item["label"] for item in first] == ["Nu", "Straks", "Vanavond", "Morgen"]
    assert all(item["safety"] == "Alleen meekijken" for item in first)
    assert all(item["action"] for item in first)
    assert all(item["reason"] for item in first)
    assert all(item["impact"] for item in first)


def test_plan_confidence_is_deterministic_and_has_known_labels():
    payload = build_read_only_cockpit_payload(summarize_cycle(_cycle()))
    degraded_payload = build_read_only_cockpit_payload({"valid_cycle": False})

    first = plan_confidence(payload)
    second = plan_confidence(payload)
    degraded = plan_confidence(degraded_payload)

    assert first == second
    assert first["label"] in {"Betrouwbaar", "Schaduwplanning", "Onvoldoende data"}
    assert degraded["label"] == "Schaduwplanning"


def test_today_summary_returns_rounded_human_values():
    payload = build_read_only_cockpit_payload(summarize_cycle(_cycle()))
    summary = today_summary(payload)

    assert summary["Batterij nu"] == "62%"
    assert summary["Verwachte eindstand"].endswith("%")
    assert summary["Zon/verbruik situatie"] == "Er is nu meer zon dan verbruik."
    assert "Alleen meekijken" in summary["Veiligheidsstatus"]


def test_json_payload_remains_raw_parseable_not_html_escaped():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))
    match = re.search(r'<script id="cockpit-payload" type="application/json">(.*?)</script>', html, re.S)

    assert match is not None
    payload_text = match.group(1)
    assert "&quot;" not in payload_text
    payload = json.loads(payload_text)
    assert payload["read_only"] is True
    assert payload["plain_planner"]["plan_card_sections"][0]["label"] == "Nu"


def test_tabs_still_render():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in ["Overview", "Plan", "Forecast", "Benchmark", "Safety"]:
        assert f">{label}<" in html
    for panel_id in ["overview", "plan", "forecast", "benchmark", "safety"]:
        assert f'data-tab-panel="{panel_id}"' in html


def test_changed_new_files_have_no_write_or_control_terms():
    offenders: list[str] = []
    for path in [
        Path("energy_brain/v2000/read_only_tesla_cockpit.py"),
        Path("tests/test_v2288_v2319_predbat_style_energy_brain_plan_card.py"),
        Path("tools/run_v2288_v2319_predbat_style_energy_brain_plan_card_smoke.sh"),
    ]:
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
            "soc_trajectory": [step["soc_percent"] for step in _steps()],
            "steps": _steps(),
        },
        "controller": {"approved": True, "execute": False, "setpoint_kw": 0.0},
        "execution": {"attempted": False},
    }


def _steps() -> list[dict]:
    reasons = [
        "charge_from_pv_surplus",
        "hold",
        "max_soc_clamped_charge",
        "max_soc_hold",
        "reserve_hold",
        "baseline_compare",
    ]
    steps = []
    for index in range(24):
        steps.append(
            {
                "index": index,
                "battery_setpoint_kw": 1.1 if index in (0, 2, 8) else 0.0,
                "soc_percent": round(62.0 + min(index, 10) * 0.7 - max(0, index - 12) * 0.25, 2),
                "reason": reasons[index % len(reasons)],
                "price": round(0.25 + (index % 6) * 0.014, 3),
                "pv_forecast": round(1.8 + (index % 8) * 0.24, 2),
                "load_forecast": round(1.0 + (index % 5) * 0.12, 2),
            }
        )
    return steps


def _scan_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
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
