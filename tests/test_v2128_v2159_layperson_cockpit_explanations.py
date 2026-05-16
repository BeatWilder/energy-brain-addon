from __future__ import annotations

import subprocess
from pathlib import Path

from energy_brain.v2000.read_only_tesla_cockpit import (
    human_action_for_step,
    human_chart_legend,
    human_reason_for_step,
    human_safety_summary,
    render_tesla_cockpit_html,
)
from energy_brain.web_ui import summarize_cycle


def test_layperson_summary_cards_render_before_chart():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Wat gebeurt er nu?",
        "Volgende slimme stap",
        "Waarom?",
        "Is dit veilig?",
        "Hoe lees ik deze grafiek?",
        "Energy Brain kijkt alleen mee.",
        "Er wordt niets aangestuurd.",
        "Technische details tonen",
        "Batterijvulling",
    ]:
        assert label in html

    assert html.index("Wat gebeurt er nu?") < html.index("Batterijvulling · SOC Trajectory")


def test_plain_dutch_badges_and_safety_text_are_visible():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    for label in [
        "Alleen meekijken",
        "Geen aansturing",
        "Veilig",
        "Schaduwplanning",
        "Ja. Deze cockpit stuurt niets aan.",
        "Geen service calls.",
        "Geen batterijcommando.",
        "Alleen lezen en uitleggen.",
    ]:
        assert label in html


def test_main_summary_has_no_raw_reason_code_label_but_technical_area_keeps_it():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))
    summary_area = html.split("Batterijvulling · SOC Trajectory", 1)[0]

    assert "reason code" not in summary_area.lower()
    assert "Technische details tonen/verbergen" in html
    assert html.index("Technische details tonen/verbergen") < html.index("reason code")


def test_selected_step_inspector_is_human_first():
    html = render_tesla_cockpit_html(summarize_cycle(_cycle()))

    assert "Stap" in html
    assert "Advies" in html
    assert "Waarom" in html
    assert "batterij laden met zonne-overschot" in html
    assert "meer zonne-energie verwacht" in html
    assert "Reden (reason code)" in html


def test_required_helper_functions_map_known_reason_codes():
    assert human_action_for_step({"reason_code": "charge_from_pv_surplus"}) == "batterij laden met zonne-overschot"
    assert human_reason_for_step({"reason_code": "charge_from_pv_surplus"}) == (
        "Er wordt meer zonne-energie verwacht dan het huis nodig heeft. Het overschot kan in de batterij."
    )
    assert human_reason_for_step({"reason_code": "max_soc_hold"}) == (
        "De batterij is vol genoeg. Energy Brain houdt hem vast en voorkomt overladen."
    )
    assert human_reason_for_step({"reason_code": "reserve_hold"}) == "Energy Brain bewaart energie als reserve."
    assert "Ja. Deze cockpit stuurt niets aan." in human_safety_summary()
    assert "Groene lijn = verwachte batterijvulling." in human_chart_legend()


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
        Path("tests/test_v2128_v2159_layperson_cockpit_explanations.py"),
        Path("tools/run_v2128_v2159_layperson_cockpit_explanations_smoke.sh"),
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
