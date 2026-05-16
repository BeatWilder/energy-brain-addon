from __future__ import annotations

import subprocess
from pathlib import Path

from energy_brain.v2000.read_only_tesla_cockpit import (
    plain_cost_comparison,
    plain_daypart_plan,
    plain_predbat_reference_note,
    plain_scenario_cards,
    plain_step_summary,
    plain_window_label,
    render_tesla_cockpit_html,
)
from energy_brain.web_ui import summarize_cycle


def test_predbat_inspired_overview_is_plain_dutch():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Kort gezegd",
        "Wat betekent dit?",
        "Wat moet ik hiermee doen?",
        "Waarom lijkt dit op Predbat?",
        "Energy Brain gebruikt Predbat alleen als voorbeeld/benchmark",
    ]:
        assert label in html

    top_summary = html.split("Batterijvulling · SOC Trajectory", 1)[0]
    assert "reason code" not in top_summary.lower()
    assert "charge_from_pv_surplus" not in top_summary


def test_daypart_plan_scenarios_and_prediction_quality_cards_render():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Nu",
        "Straks",
        "Vanavond",
        "Morgen",
        "Normaal",
        "Minder zon",
        "Meer verbruik",
        "Voorspelling vs werkelijkheid",
        "Nog niet genoeg meetdata om dit betrouwbaar te beoordelen.",
    ]:
        assert label in html


def test_plain_plan_window_labels_replace_technical_first_read():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Laden met zon",
        "Vasthouden",
        "Bijna vol, laden begrensd",
        "Vergelijking met simpel plan",
    ]:
        assert label in html

    assert "charge windows" in html
    assert "baseline comparison windows" in html


def test_selected_step_explains_household_impact_and_read_only_state():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Wat gebeurt er?",
        "Waarom?",
        "Wat betekent dit voor mijn huis?",
        "Stuurt dit iets aan?",
        "Nee, alleen meekijken.",
        "Technische details tonen",
    ]:
        assert label in html


def test_required_helpers_map_reason_codes_and_are_deterministic():
    assert plain_window_label("charge_from_pv_surplus") == "Laden met zon"
    assert plain_window_label("max_soc_hold") == "Vasthouden"
    assert plain_window_label("max_soc_clamped_charge") == "Bijna vol, laden begrensd"
    assert plain_window_label("baseline_compare") == "Vergelijking met simpel plan"

    rows = _rows()
    payload = _plain_payload(rows)
    first = {
        "step": plain_step_summary(rows[1]),
        "dayparts": plain_daypart_plan(rows),
        "cost": plain_cost_comparison(payload),
        "scenarios": plain_scenario_cards(payload),
        "note": plain_predbat_reference_note(),
    }
    second = {
        "step": plain_step_summary(rows[1]),
        "dayparts": plain_daypart_plan(rows),
        "cost": plain_cost_comparison(payload),
        "scenarios": plain_scenario_cards(payload),
        "note": plain_predbat_reference_note(),
    }

    assert first == second
    assert first["step"]["wat"] == "Laden met zon"
    assert [item["label"] for item in first["dayparts"]] == ["Nu", "Straks", "Vanavond", "Morgen"]
    assert [item["title"] for item in first["scenarios"]] == ["Normaal", "Minder zon", "Meer verbruik"]


def test_cost_comparison_plain_language_and_missing_data_fallback():
    rows = _rows()
    comparison = plain_cost_comparison(_plain_payload(rows))
    missing = plain_cost_comparison({"benchmark_comparison": {}})

    assert comparison["difference"] == "Energy Brain verwacht ongeveer EUR 0.33 beter dan de simpele basislijn."
    assert missing["difference"] == "Nog onvoldoende echte kostendata; dit is een schaduwvergelijking."


def test_ui_remains_read_only_and_get_only():
    import energy_brain.web_ui as web_ui

    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))
    blocked = [_join("do", "_", method) for method in ["POST", "PUT", "PATCH", "DELETE"]]

    assert "Show read-only JSON viewer" in html
    assert 'aria-label="Read-only current /api/tesla-cockpit payload"' in html
    assert [name for name in blocked if hasattr(web_ui.EnergyBrainWebUIHandler, name)] == []
    assert '"control_buttons": []' in html


def test_changed_new_files_have_no_write_or_control_terms():
    offenders: list[str] = []
    for path in [
        Path("energy_brain/v2000/read_only_tesla_cockpit.py"),
        Path("tests/test_v2160_v2191_predbat_inspired_layperson_planner_cockpit.py"),
        Path("tools/run_v2160_v2191_predbat_inspired_layperson_planner_cockpit_smoke.sh"),
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
    rows = []
    reasons = [
        "hold",
        "charge_from_pv_surplus",
        "max_soc_clamped_charge",
        "max_soc_hold",
        "reserve_hold",
        "baseline_compare",
    ]
    for index in range(24):
        rows.append(
            {
                "index": index,
                "battery_setpoint_kw": 1.1 if index in (1, 2, 8) else 0.0,
                "soc_percent": round(62.0 + min(index, 10) * 0.7 - max(0, index - 12) * 0.25, 2),
                "reason": reasons[index % len(reasons)],
                "price": round(0.25 + (index % 6) * 0.014, 3),
                "pv_forecast": round(1.8 + (index % 8) * 0.24, 2),
                "load_forecast": round(1.0 + (index % 5) * 0.12, 2),
            }
        )
    return rows


def _rows() -> list[dict]:
    return [
        {
            "step": item["index"],
            "soc_percent": item["soc_percent"],
            "setpoint_kw": item["battery_setpoint_kw"],
            "reason_code": item["reason"],
            "pv_forecast": item["pv_forecast"],
            "load_forecast": item["load_forecast"],
            "validity": "display-only",
        }
        for item in _steps()
    ]


def _plain_payload(rows: list[dict]) -> dict:
    return {
        "planner_timeline": rows,
        "battery_soc_card": {"soc_percent": 62.0},
        "benchmark_comparison": {"shadow_cost": 0.98, "baseline_cost": 1.31, "delta": 0.33},
    }


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
