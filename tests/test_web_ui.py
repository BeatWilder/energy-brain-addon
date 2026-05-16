from __future__ import annotations

import json
from pathlib import Path

from energy_brain.web_ui import read_latest_cycle, render_dashboard_html, summarize_cycle


def test_missing_history_file_returns_safe_status(tmp_path: Path):
    cycle = read_latest_cycle(tmp_path / "missing.jsonl")

    assert cycle == {
        "status": "safe",
        "valid_cycle": False,
        "message": "No valid cycle available",
    }


def test_empty_history_file_returns_safe_status(tmp_path: Path):
    history = tmp_path / "cycles.jsonl"
    history.write_text("", encoding="utf-8")

    cycle = read_latest_cycle(history)

    assert cycle["status"] == "safe"
    assert cycle["valid_cycle"] is False
    assert cycle["message"] == "No valid cycle available"


def test_invalid_last_json_line_returns_safe_status(tmp_path: Path):
    history = tmp_path / "cycles.jsonl"
    history.write_text(json.dumps(_cycle()) + "\nnot-json\n", encoding="utf-8")

    cycle = read_latest_cycle(history)

    assert cycle["status"] == "safe"
    assert cycle["valid_cycle"] is False
    assert cycle["message"] == "No valid cycle available"


def test_valid_latest_cycle_is_read(tmp_path: Path):
    older = _cycle(mode="shadow")
    latest = _cycle(mode="observer")
    history = tmp_path / "cycles.jsonl"
    history.write_text(
        json.dumps(older) + "\n" + json.dumps(latest) + "\n",
        encoding="utf-8",
    )

    cycle = read_latest_cycle(history)

    assert cycle["mode"] == "observer"
    assert cycle["plan"]["valid"] is True


def test_min_max_soc_summary():
    summary = summarize_cycle(_cycle(soc_trajectory=[64.0, 63.0, 70.5, 61.25]))

    assert summary["valid_cycle"] is True
    assert summary["plan"]["min_soc_percent"] == 61.25
    assert summary["plan"]["max_soc_percent"] == 70.5


def test_first_24_steps_are_rendered():
    summary = summarize_cycle(_cycle(step_count=30))
    html = render_dashboard_html(summary)

    assert "<td>0</td>" in html
    assert "<td>23</td>" in html
    assert "<td>24</td>" not in html
    assert html.count("<tr><td>") == 24


def test_dashboard_renders_required_labels_and_reasons():
    reasons = [
        "charge_from_pv_surplus",
        "max_soc_clamped_charge",
        "max_soc_hold",
        "reserve_clamped_discharge",
        "reserve_hold",
        "discharge_to_load",
        "hold",
        "bounded_no_action",
    ]
    # The dashboard intentionally renders a compact first-24-steps table.
    # Ask the helper for 24 steps and cycle through all expected reasons.
    summary = summarize_cycle(_cycle(reasons=reasons, step_count=24))
    html = render_dashboard_html(summary)

    for label in [
        "Energy Brain UI",
        "status",
        "valid_cycle",
        "mode",
        "controller.approved",
        "controller.execute",
        "execution.attempted",
        "snapshot.battery_soc_percent",
        "snapshot.pv_power_kw",
        "snapshot.household_load_kw",
        "snapshot.grid_price",
        "plan.valid",
        "plan.expected_cost",
        "plan.baseline_cost",
        "plan.delta_vs_baseline",
        "controller.setpoint_kw",
        "min_soc_percent",
        "max_soc_percent",
        "battery_setpoint_kw",
        "soc_percent",
        "reason",
    ]:
        assert label in html
    for reason in reasons:
        assert reason in html


def test_negative_delta_is_labelled_carefully():
    cycle = _cycle()
    cycle["plan"]["savings_vs_baseline"] = -0.42

    html = render_dashboard_html(summarize_cycle(cycle))

    assert "plan.delta_vs_baseline" in html
    assert "negative delta vs baseline" in html


def test_no_http_server_or_write_methods_are_exposed():
    import energy_brain.web_ui as web_ui

    public_names = {name for name in dir(web_ui) if not name.startswith("_")}

    assert "read_latest_cycle" in public_names
    assert "summarize_cycle" in public_names
    assert "render_dashboard_html" in public_names
    assert "run_server" not in public_names
    assert "create_server" not in public_names
    assert "do_POST" not in public_names
    assert "do_PUT" not in public_names
    assert "do_PATCH" not in public_names
    assert "do_DELETE" not in public_names


def test_forbidden_control_strings_not_added_to_ui_files():
    terms = _forbidden_terms()
    files = [
        Path("energy_brain/web_ui.py"),
        Path("tests/test_web_ui.py"),
    ]

    offenders = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        offenders.extend(f"{path}:{term}" for term in terms if term in text)

    assert offenders == []


def test_planner_and_controller_sources_are_unchanged():
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--", "energy_brain/planner.py", "energy_brain/controller.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""


def _cycle(
    *,
    mode: str = "observer",
    soc_trajectory: list[float] | None = None,
    step_count: int = 4,
    reasons: list[str] | None = None,
) -> dict:
    if soc_trajectory is None:
        soc_trajectory = [64.0] + [64.5 + index for index in range(step_count)]
    if reasons is None:
        reasons = ["hold"] * step_count
    steps = [
        {
            "index": index,
            "battery_setpoint_kw": 0.0,
            "soc_percent": soc_trajectory[min(index + 1, len(soc_trajectory) - 1)],
            "reason": reasons[index % len(reasons)],
        }
        for index in range(step_count)
    ]
    return {
        "mode": mode,
        "snapshot": {
            "battery_soc_percent": 64.0,
            "pv_power_kw": 2.5,
            "household_load_kw": 1.25,
            "grid_price": 0.31,
        },
        "plan": {
            "valid": True,
            "expected_cost": 1.2,
            "baseline_cost": 1.5,
            "savings_vs_baseline": 0.3,
            "soc_trajectory": soc_trajectory,
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


def _forbidden_terms() -> list[str]:
    parts = [
        ("call", "_", "service"),
        ("set", "_", "state"),
        ("/api", "/", "services"),
        ("dis", "patch"),
        ("execute", "=", "true"),
        ("battery", "_", "write"),
        ("set", "_", "battery"),
    ]
    return ["".join(part) for part in parts]
