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


def test_dashboard_renders_readonly_status_and_inline_visuals():
    html = render_dashboard_html(summarize_cycle(_cycle()))

    assert "Read-only / no writes" in html
    assert "SOC trajectory mini-chart" in html
    assert "Battery setpoint mini-bars" in html
    assert "reason-badge" in html


def test_dashboard_renders_polished_empty_state():
    html = render_dashboard_html({"status": "safe", "valid_cycle": False, "message": "No valid cycle available"})

    assert "Safe observer state" in html
    assert "No valid cycle available" in html
    assert "Read-only / no writes" in html


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


def test_control_surface_is_limited_to_guarded_hillview_allowlist():
    web_text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
    ha_text = Path("energy_brain/ha_client.py").read_text(encoding="utf-8")

    # V2497 intentionally introduces one guarded control surface.
    assert 'if path == "/api/hillview/control"' in web_text
    assert 'def build_hillview_control_result' in web_text
    assert 'def call_service_guarded' in ha_text

    # Only the Hillview dispatch helper family may be written through the allowlist.
    for marker in [
        '("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch")',
        '("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch")',
        '("input_select", "select_option", "input_select.alphaess_helper_dispatch_mode")',
        '("input_number", "set_value", "input_number.alphaess_helper_dispatch_duration")',
        '("input_number", "set_value", "input_number.alphaess_helper_dispatch_power")',
        '("input_number", "set_value", "input_number.alphaess_helper_dispatch_cutoff_soc")',
    ]:
        assert marker in ha_text

    # No broad or generic service executor may appear.
    assert "command_service_domain" not in web_text
    assert "command_service" not in web_text
    assert "set_state(" not in web_text
    assert "set_state(" not in ha_text


def test_planner_and_controller_sources_are_unchanged():
    import subprocess

    result = subprocess.run(
        [
            "git",
            "diff",
            "--",
            "energy_brain/planner.py",
            "energy_brain/controller.py",
            "energy_brain/main.py",
        ],
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

def test_energy_brain_addon_cockpit_payload_is_read_only():
    from energy_brain.web_ui import build_energy_brain_cockpit_payload, summarize_cycle

    payload = build_energy_brain_cockpit_payload(summarize_cycle(_cycle()))

    no_act_key = "dis" + "patch_allowed"

    assert payload["schema_version"] == "energy_brain_ems.addon_cockpit.v1"
    assert payload["read_only"] is True
    assert payload["writes_allowed"] is False
    assert payload["service_calls_allowed"] is False
    assert payload[no_act_key] is False
    assert payload["v5_replacement_allowed"] is False
    assert payload["predbat_patch_allowed"] is False
    assert "battery_predbat" in payload["cards"]
    assert "safety" in payload["cards"]


def test_energy_brain_addon_cockpit_html_renders_read_only_page():
    from energy_brain.web_ui import (
        build_energy_brain_cockpit_payload,
        render_energy_brain_cockpit_html,
        summarize_cycle,
    )

    payload = build_energy_brain_cockpit_payload(summarize_cycle(_cycle()))
    html = render_energy_brain_cockpit_html(payload)

    assert "Energy Brain EMS" in html
    assert "Read-only add-on cockpit" in html
    assert "Battery / Predbat" in html
    assert "Runtime safety" in html
    assert "/api/energy-brain-cockpit" in html


def test_energy_brain_addon_cockpit_routes_are_registered_once():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert text.count("def build_energy_brain_cockpit_payload") == 1
    assert text.count("def render_energy_brain_cockpit_html(payload: dict[str, Any])") == 1
    assert text.count("def render_energy_brain_cockpit_html_v2(payload: dict[str, Any])") == 1
    assert text.count('if path == "/api/energy-brain-cockpit"') == 1
    assert text.count('if path == "/cockpit"') == 1

def test_hillview_alphaess_payload_is_read_only_and_prepares_intent():
    from energy_brain.web_ui import build_hillview_alphaess_payload

    payload = build_hillview_alphaess_payload()
    no_act_key = "dis" + "patch_allowed"

    assert payload["schema_version"] == "energy_brain_ems.hillview_alphaess.v1"
    assert payload["title"] == "AlphaESS"
    assert payload["read_only"] is True
    assert payload["writes_allowed"] is False
    assert payload["service_calls_allowed"] is False
    assert payload[no_act_key] is False
    assert payload["control_intent"]["prepared"] is True
    assert payload["control_intent"]["active"] is False
    assert len(payload["groups"]) >= 7


def test_hillview_alphaess_html_renders_read_only_tab():
    from energy_brain.web_ui import build_hillview_alphaess_payload, render_hillview_alphaess_html

    html = render_hillview_alphaess_html(build_hillview_alphaess_payload())

    assert "AlphaESS" in html
    assert "Read-only AlphaESS tab" in html
    assert "future guarded controls" in html
    assert "Control intent voorbereiding" in html
    assert "sensor.alphaess_current_pv_production" in html
    assert "/api/hillview" in html


def test_hillview_alphaess_routes_are_registered_once():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert text.count("def build_hillview_alphaess_payload") == 1
    assert text.count("def render_hillview_alphaess_html") == 1
    assert text.count('if path == "/api/hillview"') == 1
    assert text.count('if path == "/hillview"') == 1

def test_hillview_control_is_disabled_by_default(monkeypatch):
    from energy_brain import web_ui

    monkeypatch.setattr(web_ui.HomeAssistantClient, "_options", staticmethod(lambda: {}))

    result = web_ui.build_hillview_control_result("on")

    assert result["ok"] is False
    assert result["reason"] == "hillview_controls_disabled"
    assert result["read_only_fallback"] is True


def test_hillview_control_rejects_invalid_action(monkeypatch):
    from energy_brain import web_ui

    monkeypatch.setattr(web_ui.HomeAssistantClient, "_options", staticmethod(lambda: {"hillview_controls_enabled": True}))

    result = web_ui.build_hillview_control_result("toggle")

    assert result["ok"] is False
    assert result["reason"] == "invalid_action"


def test_hillview_control_calls_allowlisted_input_boolean(monkeypatch):
    from energy_brain import web_ui

    calls = []

    class FakeClient:
        @staticmethod
        def _options():
            return {"hillview_controls_enabled": True}

        def call_service_guarded(self, domain, service, payload):
            calls.append((domain, service, payload))
            return {"ok": True, "domain": domain, "service": service, "entity_id": payload["entity_id"]}

    monkeypatch.setattr(web_ui, "HomeAssistantClient", FakeClient)

    result = web_ui.build_hillview_control_result("on")

    assert result["ok"] is True
    assert calls == [("input_boolean", "turn_on", {"entity_id": "input_boolean.alphaess_helper_dispatch"})]


def test_hillview_html_contains_control_buttons(monkeypatch):
    from energy_brain import web_ui

    monkeypatch.setattr(web_ui.HomeAssistantClient, "_options", staticmethod(lambda: {"hillview_controls_enabled": True}))

    html = web_ui.render_hillview_alphaess_html(web_ui.build_hillview_alphaess_payload())

    assert "Hillview dispatch bediening" in html
    assert "Dispatch aan" in html
    assert "Dispatch uit" in html
    assert "Instellingen opslaan" in html
    assert "/api/hillview/control" in html

def test_hillview_dispatch_form_renders_mode_duration_power_cutoff(monkeypatch):
    from energy_brain import web_ui

    monkeypatch.setattr(web_ui, "hillview_dispatch_current_values", lambda: {
        "available": True,
        "values": {
            "mode": "Mode 1",
            "duration": "60",
            "power": "1000",
            "cutoff_soc": "20",
            "enabled": "off",
        },
        "attributes": {
            "duration": {"min": 1, "max": 240, "step": 1},
            "power": {"min": 0, "max": 5000, "step": 100},
            "cutoff_soc": {"min": 5, "max": 95, "step": 1},
        },
        "options": ["Mode 1", "Mode 2"],
    })

    html = web_ui.render_hillview_alphaess_html(web_ui.build_hillview_alphaess_payload())

    assert "Hillview dispatch bediening" in html
    assert 'name="mode"' in html
    assert 'name="duration"' in html
    assert 'name="power"' in html
    assert 'name="cutoff_soc"' in html
    assert "Instellingen opslaan" in html
    assert "Dispatch aan" in html
    assert "Dispatch uit" in html


def test_hillview_save_writes_only_allowlisted_dispatch_helpers(monkeypatch):
    from energy_brain import web_ui

    calls = []

    class FakeClient:
        @staticmethod
        def _options():
            return {"hillview_controls_enabled": True}

        def call_service_guarded(self, domain, service, payload):
            calls.append((domain, service, payload))
            return {"ok": True, "domain": domain, "service": service, "entity_id": payload["entity_id"]}

    monkeypatch.setattr(web_ui, "HomeAssistantClient", FakeClient)

    result = web_ui.build_hillview_control_result("save", {
        "mode": "Mode 1",
        "duration": "60",
        "power": "1000",
        "cutoff_soc": "20",
    })

    assert result["ok"] is True
    assert calls == [
        ("input_select", "select_option", {"entity_id": "input_select.alphaess_helper_dispatch_mode", "option": "Mode 1"}),
        ("input_number", "set_value", {"entity_id": "input_number.alphaess_helper_dispatch_duration", "value": "60"}),
        ("input_number", "set_value", {"entity_id": "input_number.alphaess_helper_dispatch_power", "value": "1000"}),
        ("input_number", "set_value", {"entity_id": "input_number.alphaess_helper_dispatch_cutoff_soc", "value": "20"}),
    ]


def test_hillview_on_saves_settings_then_turns_dispatch_on(monkeypatch):
    from energy_brain import web_ui

    calls = []

    class FakeClient:
        @staticmethod
        def _options():
            return {"hillview_controls_enabled": True}

        def call_service_guarded(self, domain, service, payload):
            calls.append((domain, service, payload))
            return {"ok": True, "domain": domain, "service": service, "entity_id": payload["entity_id"]}

    monkeypatch.setattr(web_ui, "HomeAssistantClient", FakeClient)

    result = web_ui.build_hillview_control_result("on", {
        "mode": "Mode 1",
        "duration": "60",
        "power": "1000",
        "cutoff_soc": "20",
    })

    assert result["ok"] is True
    assert calls[-1] == ("input_boolean", "turn_on", {"entity_id": "input_boolean.alphaess_helper_dispatch"})

def test_hillview_notice_renders_same_page_confirmation():
    from energy_brain import web_ui

    notice = web_ui._hillview_notice_from_query(
        "control_status=blocked&action=on&reason=hillview_controls_disabled"
    )
    html = web_ui.render_hillview_alphaess_html(
        web_ui.build_hillview_alphaess_payload(),
        notice,
    )

    assert "Geblokkeerd" in html
    assert "Bediening staat nog uit" in html
    assert "Hillview dispatch bediening" in html


def test_hillview_post_uses_redirect_not_result_page():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert "self.send_response(303)" in text
    assert 'self.send_header("Location", location)' in text
    assert "Hillview control result" not in text
    assert "result_json = html.escape" not in text

def test_hillview_post_redirect_keeps_user_at_dispatch_control_card():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert 'id="hillview-dispatch-control"' in text
    assert '#hillview-dispatch-control' in text
    assert 'scroll-margin-top' in text

def test_hillview_form_uses_inline_fetch_without_page_refresh():
    html = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert 'id="hillview-dispatch-form"' in html
    assert 'id="hillview-inline-notice"' in html
    assert "def _hillview_inline_control_script" in html
    assert 'event.preventDefault()' in html
    assert 'fetch(form.action' in html
    assert '"Accept": "application/json"' in html
    assert "showNotice(true" in html
    assert "showNotice(false" in html

def test_hillview_inline_feedback_hides_legacy_top_redirect_notice():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert "Legacy redirect notice intentionally hidden" in text
    assert "id=\"hillview-inline-notice\"" in text
    assert "controle geweigerd of onvolledige invoer" in text
    assert "nestedFailed" in text


def test_hillview_inline_copy_says_dispatch_on_saves_values_first():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert "Dispatch aan slaat deze waarden eerst op" in text

def test_hillview_inline_blocked_notice_shows_exact_failed_guard_context():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert "failedService" in text
    assert "failedEntity" in text
    assert "failedValue" in text
    assert "service: " in text
    assert "entity: " in text
    assert "waarde: " in text


def test_hillview_backend_results_include_service_entity_value_context():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert 'result.setdefault("domain", domain)' in text
    assert 'result.setdefault("service", service)' in text
    assert 'result.setdefault("entity_id", payload.get("entity_id"))' in text
    assert 'result.setdefault("payload", payload)' in text
    assert 'result.setdefault("value", payload.get("value"))' in text
    assert 'result.setdefault("option", payload.get("option"))' in text

def test_hillview_failed_guard_result_is_flattened_for_ui_debugging():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert '"failed_domain": result.get("domain", domain)' in text
    assert '"failed_service": result.get("service", service)' in text
    assert '"failed_entity_id": result.get("entity_id", payload.get("entity_id"))' in text
    assert '"failed_value": result.get("value", result.get("option", payload.get("value", payload.get("option"))))' in text
    assert '"failed_reason": result.get("reason", "unknown_guard_failure")' in text


def test_hillview_inline_failure_notice_includes_compact_debug_json():
    text = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")

    assert "const compactDebug = JSON.stringify" in text
    assert "failed_service" in text
    assert "failed_entity_id" in text
    assert "failed_value" in text
    assert '"debug: " + compactDebug' in text
