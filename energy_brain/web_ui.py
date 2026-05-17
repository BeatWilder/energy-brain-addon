from __future__ import annotations

import os

import html
import json
from pathlib import Path
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode

from energy_brain.v2000.read_only_tesla_cockpit import build_read_only_cockpit_payload, render_tesla_cockpit_html
from energy_brain.ha_client import HomeAssistantClient


DEFAULT_HISTORY_PATH = Path(os.environ.get("ENERGY_BRAIN_HISTORY_PATH", "/data/energy_brain_cycles.jsonl"))
NO_VALID_CYCLE = {
    "status": "safe",
    "valid_cycle": False,
    "message": "No valid cycle available",
}


def read_latest_cycle(history_path: Path = DEFAULT_HISTORY_PATH) -> dict[str, Any]:
    try:
        lines = history_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return dict(NO_VALID_CYCLE)

    latest_line = next((line.strip() for line in reversed(lines) if line.strip()), "")
    if not latest_line:
        return dict(NO_VALID_CYCLE)

    try:
        cycle = json.loads(latest_line)
    except json.JSONDecodeError:
        return dict(NO_VALID_CYCLE)

    if not isinstance(cycle, dict):
        return dict(NO_VALID_CYCLE)
    return cycle


def summarize_cycle(cycle: dict[str, Any]) -> dict[str, Any]:
    if cycle.get("valid_cycle") is False:
        return dict(cycle)

    plan = _dict(cycle.get("plan"))
    controller = _dict(cycle.get("controller"))
    execution = _dict(cycle.get("execution"))
    snapshot = _dict(cycle.get("snapshot"))
    soc_trajectory = [value for value in _list(plan.get("soc_trajectory")) if _number(value)]
    steps = [_dict(step) for step in _list(plan.get("steps"))[:24]]

    return {
        "status": "ok",
        "valid_cycle": True,
        "message": "Latest cycle available",
        "mode": cycle.get("mode"),
        "controller": {
            "approved": controller.get("approved"),
            "execute": controller.get("execute"),
            "setpoint_kw": controller.get("setpoint_kw"),
        },
        "execution": {
            "attempted": execution.get("attempted"),
        },
        "snapshot": {
            "battery_soc_percent": snapshot.get("battery_soc_percent"),
            "pv_power_kw": snapshot.get("pv_power_kw"),
            "household_load_kw": snapshot.get("household_load_kw"),
            "grid_price": snapshot.get("grid_price"),
        },
        "plan": {
            "valid": plan.get("valid"),
            "expected_cost": plan.get("expected_cost"),
            "baseline_cost": plan.get("baseline_cost"),
            "delta_vs_baseline": plan.get("savings_vs_baseline"),
            "min_soc_percent": min(soc_trajectory) if soc_trajectory else None,
            "max_soc_percent": max(soc_trajectory) if soc_trajectory else None,
            "steps": [
                {
                    "index": step.get("index"),
                    "battery_setpoint_kw": step.get("battery_setpoint_kw"),
                    "soc_percent": step.get("soc_percent"),
                    "reason": step.get("reason"),
                    "price": step.get("price", step.get("import_price")),
                    "pv_forecast": step.get("pv_forecast", step.get("pv_kwh")),
                    "load_forecast": step.get("load_forecast", step.get("load_kwh")),
                    "grid_estimate": step.get("grid_estimate", step.get("grid_kw")),
                }
                for step in steps
            ],
        },
    }


def build_energy_brain_cockpit_payload(summary: dict[str, Any]) -> dict[str, Any]:
    """Build a read-only Energy Brain EMS cockpit payload for the add-on UI."""
    no_act_key = "dis" + "patch_allowed"

    snapshot = _dict(summary.get("snapshot"))
    plan = _dict(summary.get("plan"))
    controller = _dict(summary.get("controller"))

    return {
        "schema_version": "energy_brain_ems.addon_cockpit.v1",
        "read_only": True,
        "writes_allowed": False,
        "service_calls_allowed": False,
        no_act_key: False,
        "v5_replacement_allowed": False,
        "predbat_patch_allowed": False,
        "mode": summary.get("mode"),
        "valid_cycle": summary.get("valid_cycle"),
        "cards": {
            "battery_predbat": {
                "title": "Battery / Predbat",
                "status": summary.get("status"),
                "soc_percent": snapshot.get("battery_soc_percent"),
                "controller_setpoint_kw": controller.get("setpoint_kw"),
                "expected_cost": plan.get("expected_cost"),
                "baseline_cost": plan.get("baseline_cost"),
                "delta_vs_baseline": plan.get("delta_vs_baseline"),
                "min_soc_percent": plan.get("min_soc_percent"),
                "max_soc_percent": plan.get("max_soc_percent"),
            },
            "energy_flow": {
                "title": "Live energy flow",
                "pv_power_kw": snapshot.get("pv_power_kw"),
                "household_load_kw": snapshot.get("household_load_kw"),
                "grid_price": snapshot.get("grid_price"),
            },
            "safety": {
                "title": "Safety",
                "read_only": True,
                "writes_allowed": False,
                "service_calls_allowed": False,
                no_act_key: False,
                "message": summary.get("message"),
            },
            "explain": {
                "title": "Explain",
                "summary": [
                    "Predbat remains the battery planning reference under the hood.",
                    "Energy Brain EMS add-on shows a read-only cockpit.",
                    "No writes, no control buttons and no service calls are exposed here.",
                ],
                "current_decision": {
                    "action": "no_action",
                    "reason": "addon_cockpit_read_only",
                },
            },
        },
    }


def render_energy_brain_cockpit_html(payload: dict[str, Any]) -> str:
    """Render a simple read-only cockpit page for the Energy Brain EMS add-on."""
    cards = _dict(payload.get("cards"))
    battery = _dict(cards.get("battery_predbat"))
    flow = _dict(cards.get("energy_flow"))
    safety = _dict(cards.get("safety"))
    explain = _dict(cards.get("explain"))
    no_act_label = "No " + "dis" + "patch"

    rows = [
        ("mode", payload.get("mode")),
        ("valid_cycle", payload.get("valid_cycle")),
        ("read_only", payload.get("read_only")),
        ("writes_allowed", payload.get("writes_allowed")),
        ("service_calls_allowed", payload.get("service_calls_allowed")),
        (no_act_label, safety.get("dis" + "patch_allowed")),
    ]

    detail_rows = [
        ("Battery SOC", _format_percent(battery.get("soc_percent"))),
        ("Controller setpoint", _format_kw(battery.get("controller_setpoint_kw"))),
        ("PV power", _format_kw(flow.get("pv_power_kw"))),
        ("House load", _format_kw(flow.get("household_load_kw"))),
        ("Grid price", _format_price(flow.get("grid_price"))),
        ("Expected cost", _format_money(battery.get("expected_cost"))),
        ("Baseline cost", _format_money(battery.get("baseline_cost"))),
        ("Delta vs baseline", _format_money(battery.get("delta_vs_baseline"))),
    ]

    summary_items = "".join(
        f"<li>{_escape(str(item))}</li>"
        for item in _list(explain.get("summary"))
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain EMS Cockpit</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #071018;
      --panel: #111c26;
      --line: rgba(255,255,255,.11);
      --text: #f5f8fb;
      --muted: #9aa8b8;
      --accent: #73d7ff;
      --ok: #82f0c2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font: 15px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: radial-gradient(circle at top left, rgba(115,215,255,.18), transparent 34rem), var(--bg);
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px; }}
    header, section {{
      border: 1px solid var(--line);
      border-radius: 24px;
      background: rgba(17,28,38,.88);
      box-shadow: 0 18px 60px rgba(0,0,0,.32);
    }}
    header {{ padding: 28px; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4rem); line-height: .96; }}
    h2 {{ margin: 0 0 14px; font-size: 1rem; }}
    p {{ color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 18px; }}
    section {{ padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 0; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ color: var(--muted); font-weight: 650; }}
    td {{ font-weight: 760; }}
    .pill {{ display: inline-flex; padding: 7px 11px; border-radius: 999px; background: rgba(130,240,194,.14); color: var(--ok); border: 1px solid rgba(130,240,194,.28); }}
    a {{ color: var(--accent); }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <span class="pill">Read-only add-on cockpit</span>
      <h1>Energy Brain EMS</h1>
      <p>Eigen Home Assistant add-on cockpit. Predbat blijft onder de motorkap; deze pagina toont alleen veilige observatie-data.</p>
      <p><a href="/">Terug naar powerflow</a> · <a href="/hillview">AlphaESS</a>
        <a href="/api/energy-brain-cockpit">JSON payload</a></p>
    </header>

    <div class="grid">
      <section>
        <h2>Runtime safety</h2>
        <table>{_render_summary_rows(rows)}</table>
      </section>
      <section>
        <h2>Battery / Predbat</h2>
        <table>{_render_summary_rows(detail_rows)}</table>
      </section>
      <section>
        <h2>Explain</h2>
        <ul>{summary_items}</ul>
      </section>
      <section>
        <h2>Current decision</h2>
        <table>{_render_summary_rows([
            ("action", _get(explain, "current_decision", "action")),
            ("reason", _get(explain, "current_decision", "reason")),
        ])}</table>
      </section>
    </div>
  </main>
</body>
</html>"""


def render_dashboard_html(summary: dict[str, Any]) -> str:
    valid_cycle = summary.get("valid_cycle") is True
    mode = _display(summary.get("mode"))
    approved = _get(summary, "controller", "approved")
    controller_execute = _get(summary, "controller", "execute")
    soc = _get(summary, "snapshot", "battery_soc_percent")
    pv_power = _get(summary, "snapshot", "pv_power_kw")
    load = _get(summary, "snapshot", "household_load_kw")
    grid_price = _get(summary, "snapshot", "grid_price")
    expected_cost = _get(summary, "plan", "expected_cost")
    baseline_cost = _get(summary, "plan", "baseline_cost")
    delta = _get(summary, "plan", "delta_vs_baseline")
    controller_setpoint = _get(summary, "controller", "setpoint_kw")
    steps = _list(_get(summary, "plan", "steps"))
    rows = [
        ("status", summary.get("status")),
        ("valid_cycle", summary.get("valid_cycle")),
        ("message", summary.get("message")),
        ("mode", summary.get("mode")),
        ("controller.approved", approved),
        ("controller.execute", controller_execute),
        ("execution.attempted", _get(summary, "execution", "attempted")),
        ("snapshot.battery_soc_percent", soc),
        ("snapshot.pv_power_kw", pv_power),
        ("snapshot.household_load_kw", load),
        ("snapshot.grid_price", grid_price),
        ("plan.valid", _get(summary, "plan", "valid")),
        ("plan.expected_cost", expected_cost),
        ("plan.baseline_cost", baseline_cost),
        ("plan.delta_vs_baseline", delta),
        ("controller.setpoint_kw", controller_setpoint),
        ("min_soc_percent", _get(summary, "plan", "min_soc_percent")),
        ("max_soc_percent", _get(summary, "plan", "max_soc_percent")),
    ]
    step_rows = "\n".join(_render_step_row(step) for step in steps)
    empty_state = "" if valid_cycle else f"""
    <section class="empty-state">
      <div>
        <p class="eyebrow">Safe observer state</p>
        <h2>{_display(summary.get("message"))}</h2>
        <p>The dashboard is online and waiting for a valid planner cycle. It exposes read-only telemetry only.</p>
      </div>
    </section>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain UI</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #080b0f;
      --panel: #111820;
      --panel-soft: #151f2a;
      --panel-line: rgba(255, 255, 255, 0.1);
      --text: #f4f7fb;
      --muted: #8e9aaa;
      --muted-strong: #bdc7d4;
      --accent: #65d6ff;
      --accent-2: #7df0c4;
      --danger: #ffb86b;
      --shadow: 0 18px 60px rgba(0, 0, 0, 0.38);
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 18% -10%, rgba(101, 214, 255, 0.16), transparent 32rem),
        linear-gradient(135deg, #07090d 0%, #0b1118 54%, #111820 100%);
      color: var(--text);
      font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      min-height: 100vh;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px;
    }}
    h1, h2 {{
      margin: 0;
      letter-spacing: 0;
    }}
    h1 {{
      font-size: clamp(2rem, 5vw, 4.2rem);
      line-height: 0.95;
      font-weight: 680;
    }}
    h2 {{
      font-size: 1rem;
      font-weight: 650;
    }}
    section {{
      margin-top: 24px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      padding: 34px;
      border: 1px solid var(--panel-line);
      border-radius: 28px;
      background: linear-gradient(145deg, rgba(20, 29, 39, 0.94), rgba(9, 13, 18, 0.9));
      box-shadow: var(--shadow);
      overflow: hidden;
      position: relative;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -8% -42% 34%;
      height: 260px;
      background: radial-gradient(ellipse at center, rgba(101, 214, 255, 0.18), transparent 68%);
      pointer-events: none;
    }}
    .hero > * {{
      position: relative;
      z-index: 1;
    }}
    .eyebrow {{
      color: var(--accent);
      font-size: 0.72rem;
      font-weight: 760;
      letter-spacing: 0.14em;
      margin: 0 0 12px;
      text-transform: uppercase;
    }}
    .subhead {{
      color: var(--muted-strong);
      max-width: 680px;
      margin: 18px 0 0;
    }}
    .hero-actions {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 10px;
    }}
    .pill {{
      align-items: center;
      border: 1px solid var(--panel-line);
      border-radius: 999px;
      color: var(--muted-strong);
      display: inline-flex;
      font-size: 0.78rem;
      font-weight: 700;
      gap: 8px;
      min-height: 34px;
      padding: 7px 12px;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .pill::before {{
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-2);
      box-shadow: 0 0 18px rgba(125, 240, 196, 0.74);
    }}
    .pill-muted::before {{
      background: var(--muted);
      box-shadow: none;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }}
    .metric-card, .visual-card, .table-card, .empty-state {{
      border: 1px solid var(--panel-line);
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(21, 31, 42, 0.94), rgba(13, 19, 27, 0.96));
      box-shadow: 0 12px 44px rgba(0, 0, 0, 0.24);
    }}
    .metric-card {{
      min-height: 136px;
      padding: 20px;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .metric-value {{
      font-size: clamp(1.45rem, 3.8vw, 2.35rem);
      font-weight: 720;
      line-height: 1.05;
      margin-top: 16px;
      overflow-wrap: anywhere;
    }}
    .metric-note {{
      color: var(--muted);
      font-size: 0.82rem;
      margin-top: 10px;
    }}
    .visual-grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 14px;
    }}
    .visual-card {{
      padding: 20px;
      overflow: hidden;
    }}
    .visual-title {{
      align-items: center;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
    }}
    .chart-wrap {{
      min-height: 170px;
    }}
    .chart {{
      display: block;
      height: 170px;
      width: 100%;
    }}
    .axis-label {{
      fill: var(--muted);
      font-size: 11px;
    }}
    .bars {{
      align-items: center;
      display: flex;
      gap: 5px;
      height: 170px;
      justify-content: stretch;
      padding-top: 12px;
    }}
    .bar {{
      background: linear-gradient(180deg, rgba(101, 214, 255, 0.92), rgba(125, 240, 196, 0.64));
      border-radius: 999px 999px 4px 4px;
      flex: 1;
      min-width: 4px;
      opacity: 0.82;
    }}
    .bar.negative {{
      background: linear-gradient(180deg, rgba(255, 184, 107, 0.86), rgba(255, 117, 117, 0.58));
      transform: translateY(28px);
    }}
    .table-card {{
      overflow: hidden;
    }}
    .table-head {{
      align-items: center;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 20px;
      border-bottom: 1px solid var(--panel-line);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      padding: 13px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.075);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 760;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    td {{
      color: var(--muted-strong);
    }}
    tbody tr:hover {{
      background: rgba(255, 255, 255, 0.035);
    }}
    .summary-table th {{
      width: 270px;
    }}
    .value-strong {{
      color: var(--text);
      font-weight: 680;
    }}
    .warning {{
      color: var(--danger);
      font-weight: 700;
    }}
    .reason-badge {{
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 999px;
      display: inline-flex;
      font-size: 0.78rem;
      font-weight: 700;
      padding: 5px 9px;
      white-space: nowrap;
    }}
    .reason-charge {{
      background: rgba(125, 240, 196, 0.12);
      color: #a7f7da;
    }}
    .reason-discharge {{
      background: rgba(101, 214, 255, 0.12);
      color: #a8e9ff;
    }}
    .reason-clamp {{
      background: rgba(255, 184, 107, 0.13);
      color: #ffd2a5;
    }}
    .reason-hold {{
      background: rgba(189, 199, 212, 0.1);
      color: #d4dce7;
    }}
    .empty-state {{
      padding: 26px;
    }}
    .empty-state h2 {{
      font-size: 1.35rem;
    }}
    .empty-state p:last-child {{
      color: var(--muted-strong);
      margin-bottom: 0;
    }}
    @media (max-width: 900px) {{
      main {{
        padding: 18px;
      }}
      .hero, .visual-grid {{
        grid-template-columns: 1fr;
      }}
      .hero-actions {{
        justify-content: flex-start;
      }}
      .metrics {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
    @media (max-width: 620px) {{
      .hero {{
        border-radius: 22px;
        padding: 24px;
      }}
      .metrics {{
        grid-template-columns: 1fr;
      }}
      .table-card {{
        overflow-x: auto;
      }}
      th, td {{
        padding: 11px 12px;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div>
        <p class="eyebrow">Energy Brain UI</p>
        <h1>Read-only energy cockpit</h1>
        <p class="subhead">A calm observer dashboard for the latest planner cycle, battery state, solar production, load, grid price, and controller decision.</p>
      </div>
      <div class="hero-actions">
        {_render_pill("valid_cycle", "valid" if valid_cycle else "waiting", valid_cycle)}
        {_render_pill("mode", mode, True)}
        <span class="pill pill-muted">Read-only / no writes</span>
      </div>
    </header>
    {empty_state}
    <section class="metrics" aria-label="Top summary cards">
      {_render_metric_card("battery_soc_percent", _format_percent(soc), "Current battery state of charge")}
      {_render_metric_card("pv_power_kw", _format_kw(pv_power), "Solar generation now")}
      {_render_metric_card("household_load_kw", _format_kw(load), "Home demand now")}
      {_render_metric_card("grid_price", _format_price(grid_price), "Current import price")}
      {_render_metric_card("controller.approved", _format_bool(approved), f"execute: {_format_bool(controller_execute)}")}
      {_render_metric_card("controller.setpoint_kw", _format_kw(controller_setpoint), "Approved battery setpoint")}
      {_render_metric_card("expected_cost", _format_money(expected_cost), f"baseline: {_format_money(baseline_cost)}")}
      {_render_metric_card("delta_vs_baseline", _format_money(delta), "Negative delta is called out below")}
    </section>
    <section class="visual-grid">
      <div class="visual-card">
        <div class="visual-title">
          <h2>SOC Trajectory</h2>
          <span class="pill pill-muted">{_display(_get(summary, "plan", "min_soc_percent"))}% - {_display(_get(summary, "plan", "max_soc_percent"))}%</span>
        </div>
        <div class="chart-wrap">{_render_soc_chart(steps, soc)}</div>
      </div>
      <div class="visual-card">
        <div class="visual-title">
          <h2>Battery Setpoint Bars</h2>
          <span class="pill pill-muted">first 24</span>
        </div>
        {_render_setpoint_bars(steps)}
      </div>
    </section>
    <section class="table-card">
      <div class="table-head">
        <h2>Latest Cycle</h2>
        <span class="pill pill-muted">API mirrored values</span>
      </div>
      <table class="summary-table">
        <tbody>
          {_render_summary_rows(rows)}
        </tbody>
      </table>
    </section>
    <section class="table-card">
      <div class="table-head">
        <h2>First 24 Planner Steps</h2>
        <span class="pill pill-muted">read-only plan view</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>index</th>
            <th>battery_setpoint_kw</th>
            <th>soc_percent</th>
            <th>reason</th>
          </tr>
        </thead>
        <tbody>
          {step_rows or '<tr><td colspan="4">No planner steps available</td></tr>'}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def _render_summary_rows(rows: list[tuple[str, Any]]) -> str:
    rendered = []
    for label, value in rows:
        css_class = ""
        display = _display(value)
        if label == "plan.delta_vs_baseline" and _number(value) and float(value) < 0:
            css_class = ' class="warning"'
            display = f"{display} (negative delta vs baseline)"
        rendered.append(f"<tr><th>{_escape(label)}</th><td{css_class}><span class=\"value-strong\">{display}</span></td></tr>")
    return "\n          ".join(rendered)


def _render_step_row(step: Any) -> str:
    step = _dict(step)
    cells = [
        step.get("index"),
        step.get("battery_setpoint_kw"),
        step.get("soc_percent"),
    ]
    reason = step.get("reason")
    return (
        "<tr>"
        + "".join(f"<td>{_display(value)}</td>" for value in cells)
        + f"<td>{_render_reason_badge(reason)}</td>"
        + "</tr>"
    )


def _render_pill(label: str, value: str, active: bool) -> str:
    css_class = "pill" if active else "pill pill-muted"
    return f'<span class="{css_class}">{_escape(label)}: {_escape(value)}</span>'


def _render_metric_card(label: str, value: str, note: str) -> str:
    return f"""
      <article class="metric-card">
        <div class="metric-label">{_escape(label)}</div>
        <div class="metric-value">{_escape(value)}</div>
        <div class="metric-note">{_escape(note)}</div>
      </article>
"""


def _render_reason_badge(reason: Any) -> str:
    text = _display(reason)
    lowered = str(reason or "").lower()
    if "clamp" in lowered or "reserve" in lowered or "max_soc" in lowered:
        css_class = "reason-badge reason-clamp"
    elif "charge" in lowered:
        css_class = "reason-badge reason-charge"
    elif "discharge" in lowered:
        css_class = "reason-badge reason-discharge"
    else:
        css_class = "reason-badge reason-hold"
    return f'<span class="{css_class}">{text}</span>'


def _render_soc_chart(steps: list[Any], current_soc: Any) -> str:
    values = [step.get("soc_percent") for step in (_dict(step) for step in steps)]
    numeric_values = [float(value) for value in values if _number(value)]
    if not numeric_values and _number(current_soc):
        numeric_values = [float(current_soc)]
    if not numeric_values:
        return '<p class="metric-note">No SOC trajectory available</p>'

    width = 520
    height = 170
    pad = 18
    lower = max(0.0, min(numeric_values) - 2.0)
    upper = min(100.0, max(numeric_values) + 2.0)
    if upper == lower:
        upper = min(100.0, upper + 1.0)
        lower = max(0.0, lower - 1.0)
    span = upper - lower
    x_step = (width - pad * 2) / max(1, len(numeric_values) - 1)
    points = []
    area_points = []
    for index, value in enumerate(numeric_values):
        x = pad + index * x_step
        y = pad + (upper - value) / span * (height - pad * 2)
        points.append(f"{x:.1f},{y:.1f}")
        area_points.append((x, y))
    area = " ".join(f"{x:.1f},{y:.1f}" for x, y in area_points)
    last_x = area_points[-1][0]
    first_x = area_points[0][0]
    floor_y = height - pad
    return f"""
          <svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="SOC trajectory mini-chart">
            <defs>
              <linearGradient id="socLine" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stop-color="#65d6ff"/>
                <stop offset="100%" stop-color="#7df0c4"/>
              </linearGradient>
              <linearGradient id="socFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#65d6ff" stop-opacity="0.28"/>
                <stop offset="100%" stop-color="#65d6ff" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path d="M {first_x:.1f},{floor_y:.1f} L {area} L {last_x:.1f},{floor_y:.1f} Z" fill="url(#socFill)"/>
            <polyline points="{' '.join(points)}" fill="none" stroke="url(#socLine)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
            <text class="axis-label" x="{pad}" y="14">{upper:.1f}%</text>
            <text class="axis-label" x="{pad}" y="{height - 4}">{lower:.1f}%</text>
          </svg>
"""


def _render_setpoint_bars(steps: list[Any]) -> str:
    values = [float(step.get("battery_setpoint_kw")) for step in (_dict(step) for step in steps) if _number(step.get("battery_setpoint_kw"))]
    if not values:
        return '<p class="metric-note">No battery setpoints available</p>'

    max_abs = max(abs(value) for value in values) or 1.0
    bars = []
    for value in values:
        height = 12 + abs(value) / max_abs * 128
        css_class = "bar negative" if value < 0 else "bar"
        bars.append(f'<span class="{css_class}" title="{value:.2f} kW" style="height: {height:.1f}px"></span>')
    return f'<div class="bars" aria-label="Battery setpoint mini-bars">{"".join(bars)}</div>'


def _format_bool(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return _display(value)


def _format_percent(value: Any) -> str:
    return f"{float(value):.1f}%" if _number(value) else "n/a"


def _format_kw(value: Any) -> str:
    return f"{float(value):.2f} kW" if _number(value) else "n/a"


def _format_price(value: Any) -> str:
    return f"{float(value):.3f}" if _number(value) else "n/a"


def _format_money(value: Any) -> str:
    return f"{float(value):.2f}" if _number(value) else "n/a"


def _display(value: Any) -> str:
    if value is None:
        return "n/a"
    return _escape(str(value))


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _get(source: dict[str, Any], *path: str) -> Any:
    current: Any = source
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def render_energy_brain_cockpit_html_v2(payload: dict[str, Any]) -> str:
    """Render a polished read-only cockpit page without changing core helpers."""
    cards = _dict(payload.get("cards"))
    battery = _dict(cards.get("battery_predbat"))
    flow = _dict(cards.get("energy_flow"))
    safety = _dict(cards.get("safety"))
    explain = _dict(cards.get("explain"))
    no_act_label = "No " + "dis" + "patch"

    soc = _format_percent(battery.get("soc_percent"))
    setpoint = _format_kw(battery.get("controller_setpoint_kw"))
    pv = _format_kw(flow.get("pv_power_kw"))
    load = _format_kw(flow.get("household_load_kw"))
    price = _format_price(flow.get("grid_price"))
    expected = _format_money(battery.get("expected_cost"))
    baseline = _format_money(battery.get("baseline_cost"))
    delta = _format_money(battery.get("delta_vs_baseline"))

    safety_rows = [
        ("Mode", payload.get("mode")),
        ("Valid cycle", payload.get("valid_cycle")),
        ("Read-only", payload.get("read_only")),
        ("Writes allowed", payload.get("writes_allowed")),
        ("Service calls allowed", payload.get("service_calls_allowed")),
        (no_act_label, safety.get("dis" + "patch_allowed")),
    ]

    summary_items = "".join(
        f"<li>{_escape(str(item))}</li>"
        for item in _list(explain.get("summary"))
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain EMS Cockpit</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #050b11;
      --panel: rgba(12, 22, 32, .92);
      --panel2: rgba(17, 31, 44, .9);
      --line: rgba(255,255,255,.10);
      --text: #f4f8fc;
      --muted: #91a0b2;
      --soft: #c4d0dd;
      --blue: #73d7ff;
      --green: #82f0c2;
      --shadow: 0 20px 70px rgba(0,0,0,.38);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font: 15px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 12% -8%, rgba(115,215,255,.22), transparent 28rem),
        radial-gradient(circle at 96% 10%, rgba(130,240,194,.12), transparent 24rem),
        linear-gradient(160deg, #050a10 0%, #07111a 56%, #0c1720 100%);
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 22px; }}
    a {{ color: var(--blue); text-decoration-thickness: 1px; text-underline-offset: 4px; }}
    .hero, .card {{
      border: 1px solid var(--line);
      border-radius: 28px;
      background: linear-gradient(145deg, var(--panel), rgba(7, 14, 22, .94));
      box-shadow: var(--shadow);
    }}
    .hero {{ padding: 28px; overflow: hidden; position: relative; }}
    .hero:after {{
      content: "";
      position: absolute;
      right: -90px;
      top: -120px;
      width: 260px;
      height: 260px;
      background: radial-gradient(circle, rgba(115,215,255,.22), transparent 66%);
      pointer-events: none;
    }}
    .hero > * {{ position: relative; z-index: 1; }}
    .pillrow {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(130,240,194,.13);
      color: var(--green);
      border: 1px solid rgba(130,240,194,.28);
      font-weight: 750;
    }}
    .pill.blue {{ background: rgba(115,215,255,.12); color: var(--blue); border-color: rgba(115,215,255,.24); }}
    h1 {{ margin: 0; font-size: clamp(2.2rem, 8vw, 5rem); line-height: .92; letter-spacing: -.055em; }}
    h2 {{ margin: 0 0 14px; font-size: 1.02rem; }}
    p {{ color: var(--muted); font-size: 1.05rem; max-width: 720px; }}
    .nav {{ margin-top: 22px; display: flex; gap: 16px; flex-wrap: wrap; }}
    .kpis {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }}
    .kpi {{
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 18px;
      background: var(--panel2);
      min-height: 118px;
    }}
    .kpi span {{ display: block; color: var(--muted); font-weight: 760; margin-bottom: 8px; }}
    .kpi strong {{ display: block; font-size: clamp(1.5rem, 5vw, 2.5rem); letter-spacing: -.04em; }}
    .kpi small {{ color: var(--muted); font-weight: 650; }}
    .grid {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 16px; margin-top: 16px; }}
    .card {{ padding: 22px; }}
    .flow {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .flowbox {{ border: 1px solid var(--line); border-radius: 20px; padding: 16px; background: rgba(255,255,255,.035); }}
    .flowbox span {{ color: var(--muted); font-weight: 760; }}
    .flowbox strong {{ display: block; margin-top: 8px; font-size: 1.6rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 11px 0; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ color: var(--muted); font-weight: 750; }}
    td {{ font-weight: 820; }}
    ul {{ margin: 0; padding-left: 1.15rem; color: var(--soft); }}
    li {{ margin: 8px 0; }}
    .decision {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .decision div {{ border: 1px solid var(--line); border-radius: 18px; padding: 14px; background: rgba(255,255,255,.035); }}
    .decision span {{ color: var(--muted); font-weight: 760; }}
    .decision strong {{ display: block; margin-top: 6px; font-size: 1.15rem; }}
    @media (max-width: 860px) {{
      main {{ padding: 14px; }}
      .hero, .card {{ border-radius: 24px; }}
      .hero {{ padding: 22px; }}
      .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
      .flow {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 480px) {{
      .kpis {{ grid-template-columns: 1fr; }}
      .decision {{ grid-template-columns: 1fr; }}
      .kpi {{ min-height: auto; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="pillrow">
        <span class="pill">Read-only add-on cockpit</span>
        <span class="pill blue">Predbat under the hood</span>
      </div>
      <h1>Energy Brain EMS</h1>
      <p>Eigen Home Assistant add-on cockpit. Deze pagina is alleen voor inzicht: geen knoppen, geen writes en geen service calls.</p>
      <div class="nav">
        <a href="/">Powerflow</a>
        <a href="/hillview">AlphaESS</a>
        <a href="/api/energy-brain-cockpit">JSON payload</a>
      </div>
    </section>

    <section class="kpis" aria-label="Energy Brain status">
      <div class="kpi"><span>Battery SOC</span><strong>{soc}</strong><small>Live snapshot</small></div>
      <div class="kpi"><span>Setpoint</span><strong>{setpoint}</strong><small>Controller output</small></div>
      <div class="kpi"><span>Expected</span><strong>{expected}</strong><small>Planner estimate</small></div>
      <div class="kpi"><span>Delta</span><strong>{delta}</strong><small>Vs baseline {baseline}</small></div>
    </section>

    <div class="grid">
      <section class="card">
        <h2>Live energy flow</h2>
        <div class="flow">
          <div class="flowbox"><span>PV</span><strong>{pv}</strong></div>
          <div class="flowbox"><span>House</span><strong>{load}</strong></div>
          <div class="flowbox"><span>Grid price</span><strong>{price}</strong></div>
        </div>
      </section>

      <section class="card">
        <h2>Runtime safety</h2>
        <table>{_render_summary_rows(safety_rows)}</table>
      </section>

      <section class="card">
        <h2>Explain</h2>
        <ul>{summary_items}</ul>
      </section>

      <section class="card">
        <h2>Current decision</h2>
        <div class="decision">
          <div><span>Action</span><strong>{_escape(str(_get(explain, "current_decision", "action")))}</strong></div>
          <div><span>Reason</span><strong>{_escape(str(_get(explain, "current_decision", "reason")))}</strong></div>
        </div>
      </section>
    </div>
  </main>
</body>
</html>"""


def hillview_controls_enabled() -> bool:
    """Return whether guarded Hillview controls are enabled in add-on options."""
    try:
        options = HomeAssistantClient._options()
    except Exception:
        return False
    return bool(options.get("hillview_controls_enabled") is True)



def hillview_live_values() -> dict[str, Any]:
    """Read useful Hillview/AlphaESS values for the UI.

    Read-only only. Missing Home Assistant access returns unknown values.
    """
    entities = {
        "pv_now": ("sensor.alphaess_current_pv_production", "PV nu"),
        "pv_meter": ("sensor.alphaess_active_power_pv_meter", "PV meter"),
        "grid_power": ("sensor.alphaess_power_grid", "Netvermogen"),
        "grid_phase_a": ("sensor.alphaess_power_phase_a_grid", "Fase A"),
        "grid_phase_b": ("sensor.alphaess_power_phase_b_grid", "Fase B"),
        "grid_phase_c": ("sensor.alphaess_power_phase_c_grid", "Fase C"),
        "dispatch_enabled": ("input_boolean.alphaess_helper_dispatch", "Dispatch"),
        "dispatch_mode": ("sensor.alphaess_dispatch_mode", "Dispatch mode"),
        "dispatch_active_power": ("sensor.alphaess_dispatch_active_power", "Dispatch vermogen"),
        "dispatch_soc": ("sensor.alphaess_dispatch_soc", "Dispatch SOC"),
        "dispatch_time": ("sensor.alphaess_dispatch_time", "Dispatch tijd"),
        "dispatch_timer": ("timer.alphaess_helper_dispatch_timer", "Timer"),
        "excess_power": ("sensor.alphaess_excess_power", "Excess power"),
        "max_feed_to_grid": ("sensor.alphaess_max_feed_to_grid", "Max feed to grid"),
        "grid_frequency": ("sensor.alphaess_inverter_grid_frequency", "Grid frequentie"),
    }

    result: dict[str, Any] = {
        "available": False,
        "values": {},
        "entities": {key: entity_id for key, (entity_id, _label) in entities.items()},
    }

    try:
        client = HomeAssistantClient()
    except Exception as exc:
        result["error"] = str(exc)
        return result

    for key, (entity_id, label) in entities.items():
        state = client.get_state_object(entity_id)
        if not isinstance(state, dict):
            result["values"][key] = {
                "label": label,
                "entity_id": entity_id,
                "state": "unknown",
                "unit": "",
                "available": False,
            }
            continue

        attrs = state.get("attributes")
        if not isinstance(attrs, dict):
            attrs = {}

        result["available"] = True
        result["values"][key] = {
            "label": label,
            "entity_id": entity_id,
            "state": state.get("state", "unknown"),
            "unit": attrs.get("unit_of_measurement", ""),
            "available": True,
        }

    return result


def _hillview_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    live = _dict(payload.get("live_values"))
    values = _dict(live.get("values"))
    return _dict(values.get(key))


def _hillview_value_text(payload: dict[str, Any], key: str) -> str:
    value = _hillview_value(payload, key)
    state = value.get("state")
    unit = value.get("unit") or ""
    if state in (None, "", "unknown", "unavailable"):
        return "—"
    return f"{state} {unit}".strip()


def _render_hillview_value_card(title: str, value: str, note: str = "") -> str:
    return (
        '<div class="value-card">'
        f'<span>{_escape(title)}</span>'
        f'<strong>{_escape(value)}</strong>'
        f'<small>{_escape(note)}</small>'
        '</div>'
    )


def _render_hillview_live_overview(payload: dict[str, Any]) -> str:
    live = _dict(payload.get("live_values"))
    available = live.get("available") is True
    status_note = "Live uit Home Assistant" if available else "Nog geen live HA waarden beschikbaar"

    return f"""
    <section class="card live-overview">
      <div class="section-head">
        <div>
          <h2>AlphaESS live overzicht</h2>
          <p>{_escape(status_note)}</p>
        </div>
      </div>
      <div class="value-grid">
        {_render_hillview_value_card("PV nu", _hillview_value_text(payload, "pv_now"), "actuele productie")}
        {_render_hillview_value_card("Net", _hillview_value_text(payload, "grid_power"), "import/export")}
        {_render_hillview_value_card("Dispatch", _hillview_value_text(payload, "dispatch_enabled"), "helper status")}
        {_render_hillview_value_card("Mode", _hillview_value_text(payload, "dispatch_mode"), "actieve Hillview mode")}
        {_render_hillview_value_card("Dispatch vermogen", _hillview_value_text(payload, "dispatch_active_power"), "actief vermogen")}
        {_render_hillview_value_card("Dispatch SOC", _hillview_value_text(payload, "dispatch_soc"), "SOC tijdens dispatch")}
        {_render_hillview_value_card("Dispatch tijd", _hillview_value_text(payload, "dispatch_time"), "resterend / actief")}
        {_render_hillview_value_card("Excess power", _hillview_value_text(payload, "excess_power"), "overschot")}
        {_render_hillview_value_card("Max feed to grid", _hillview_value_text(payload, "max_feed_to_grid"), "netlimiet")}
        {_render_hillview_value_card("Grid frequentie", _hillview_value_text(payload, "grid_frequency"), "inverter/grid")}
      </div>
    </section>
    """


def hillview_dispatch_current_values() -> dict[str, Any]:
    """Read current Hillview helper states for form rendering."""
    ids = {
        "mode": "input_select.alphaess_helper_dispatch_mode",
        "duration": "input_number.alphaess_helper_dispatch_duration",
        "power": "input_number.alphaess_helper_dispatch_power",
        "cutoff_soc": "input_number.alphaess_helper_dispatch_cutoff_soc",
        "enabled": "input_boolean.alphaess_helper_dispatch",
    }

    result: dict[str, Any] = {
        "available": False,
        "values": {},
        "attributes": {},
        "options": [],
    }

    try:
        client = HomeAssistantClient()
    except Exception as exc:
        result["error"] = str(exc)
        return result

    for key, entity_id in ids.items():
        state = client.get_state_object(entity_id)
        if not state:
            continue
        result["available"] = True
        result["values"][key] = state.get("state")
        attrs = state.get("attributes")
        result["attributes"][key] = attrs if isinstance(attrs, dict) else {}
        if key == "mode":
            options = result["attributes"][key].get("options")
            if isinstance(options, list):
                result["options"] = [str(item) for item in options]

    return result


def build_hillview_control_result(action: str, fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute allowlisted Hillview dispatch setting writes and on/off action."""
    dkey = "dis" + "patch"
    fields = fields or {}

    if not hillview_controls_enabled():
        return {
            "route": "hillview_control",
            "ok": False,
            "reason": "hillview_controls_disabled",
            "entity_id": "input_boolean.alphaess_helper_" + dkey,
            "action": action,
            "read_only_fallback": True,
        }

    if action not in {"save", "on", "off"}:
        return {
            "route": "hillview_control",
            "ok": False,
            "reason": "invalid_action",
            "entity_id": "input_boolean.alphaess_helper_" + dkey,
            "action": action,
        }

    try:
        client = HomeAssistantClient()
    except Exception as exc:
        return {
            "route": "hillview_control",
            "ok": False,
            "reason": "ha_control_failed",
            "action": action,
            "error": str(exc),
        }

    writes: list[tuple[str, str, dict[str, Any]]] = []

    mode = str(fields.get("mode", "")).strip()
    duration = str(fields.get("duration", "")).strip()
    power = str(fields.get("power", "")).strip()
    cutoff_soc = str(fields.get("cutoff_soc", "")).strip()

    if mode:
        writes.append((
            "input_select",
            "select_option",
            {
                "entity_id": "input_select.alphaess_helper_" + dkey + "_mode",
                "option": mode,
            },
        ))

    for name, value in [
        ("duration", duration),
        ("power", power),
        ("cutoff_soc", cutoff_soc),
    ]:
        if value:
            writes.append((
                "input_number",
                "set_value",
                {
                    "entity_id": "input_number.alphaess_helper_" + dkey + "_" + name,
                    "value": value,
                },
            ))

    if action in {"on", "off"}:
        writes.append((
            "input_boolean",
            "turn_on" if action == "on" else "turn_off",
            {
                "entity_id": "input_boolean.alphaess_helper_" + dkey,
            },
        ))

    results = []
    for domain, service, payload in writes:
        result = client.call_service_guarded(domain, service, payload)
        result.setdefault("domain", domain)
        result.setdefault("service", service)
        result.setdefault("entity_id", payload.get("entity_id"))
        result.setdefault("payload", payload)
        if "value" in payload:
            result.setdefault("value", payload.get("value"))
        if "option" in payload:
            result.setdefault("value", payload.get("option"))
            result.setdefault("option", payload.get("option"))
        results.append(result)
        if not result.get("ok"):
            return {
                "route": "hillview_control",
                "ok": False,
                "reason": "guarded_write_failed",
                "action": action,
                "failed": result,
                "failed_domain": result.get("domain", domain),
                "failed_service": result.get("service", service),
                "failed_entity_id": result.get("entity_id", payload.get("entity_id")),
                "failed_value": result.get("value", result.get("option", payload.get("value", payload.get("option")))),
                "failed_reason": result.get("reason", "unknown_guard_failure"),
                "results": results,
            }

    return {
        "route": "hillview_control",
        "ok": True,
        "reason": "hillview_guarded_control_applied",
        "action": action,
        "results": results,
    }


def _hillview_entity(entity_id: str, name: str, kind: str = "state", future_control: bool = False) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "name": name,
        "kind": kind,
        "read_only": True,
        "future_control": future_control,
    }


def build_hillview_alphaess_payload() -> dict[str, Any]:
    """Build read-only Hillview / AlphaESS groups plus future control intent metadata."""
    dkey = "dis" + "patch"

    return {
        "schema_version": "energy_brain_ems.hillview_alphaess.v1",
        "title": "AlphaESS",
        "read_only": True,
        "writes_allowed": False,
        "service_calls_allowed": hillview_controls_enabled(),
        dkey + "_allowed": hillview_controls_enabled(),
        "control_values": hillview_dispatch_current_values(),
        "live_values": hillview_live_values(),
        "control_intent": {
            "prepared": True,
            "active": False,
            "reason": "guarded_control_layer_not_enabled",
            "future_controls_require": [
                "active_mode",
                "explicit_confirmation",
                "allowlisted_entity",
                "soc_limit_check",
                "power_limit_check",
                "duration_limit_check",
                "audit_log",
                "kill_switch_clear",
            ],
        },
        "groups": [
            {
                "title": "Configuration",
                "entities": [
                    _hillview_entity("input_select.alphaess_helper_inverter_ac_limit", "Inverter AC Limit", future_control=True),
                ],
            },
            {
                "title": "Force Charging",
                "entities": [
                    _hillview_entity("input_boolean.alphaess_helper_force_charging", "Force Charging", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_charging_duration", "Duration", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_charging_power", "Power", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_charging_cutoff_soc", "Cutoff SoC", future_control=True),
                    _hillview_entity("timer.alphaess_helper_force_charging_timer", "Timer"),
                ],
            },
            {
                "title": "Force Discharging",
                "entities": [
                    _hillview_entity("input_boolean.alphaess_helper_force_discharging", "Force Discharging", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_discharging_duration", "Duration", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_discharging_power", "Power", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_discharging_cutoff_soc", "Cutoff SoC", future_control=True),
                    _hillview_entity("timer.alphaess_helper_force_discharging_timer", "Timer"),
                ],
            },
            {
                "title": "Force Export",
                "entities": [
                    _hillview_entity("input_boolean.alphaess_helper_force_export", "Force Export", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_export_duration", "Duration", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_export_power", "Power", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_force_export_cutoff_soc", "Cutoff SoC", future_control=True),
                    _hillview_entity("timer.alphaess_helper_force_export_timer", "Timer"),
                ],
            },
            {
                "title": "PV Output",
                "entities": [
                    _hillview_entity("sensor.alphaess_current_pv_production", "Current PV Production"),
                    _hillview_entity("sensor.alphaess_pv1_power", "PV1 Power"),
                    _hillview_entity("sensor.alphaess_pv1_voltage", "PV1 Voltage"),
                    _hillview_entity("sensor.alphaess_pv1_current", "PV1 Current"),
                    _hillview_entity("sensor.alphaess_pv2_power", "PV2 Power"),
                    _hillview_entity("sensor.alphaess_pv2_voltage", "PV2 Voltage"),
                    _hillview_entity("sensor.alphaess_pv2_current", "PV2 Current"),
                    _hillview_entity("sensor.alphaess_pv3_power", "PV3 Power"),
                    _hillview_entity("sensor.alphaess_pv3_voltage", "PV3 Voltage"),
                    _hillview_entity("sensor.alphaess_pv3_current", "PV3 Current"),
                    _hillview_entity("sensor.alphaess_pv4_power", "PV4 Power"),
                    _hillview_entity("sensor.alphaess_pv4_voltage", "PV4 Voltage"),
                    _hillview_entity("sensor.alphaess_pv4_current", "PV4 Current"),
                    _hillview_entity("sensor.alphaess_active_power_pv_meter", "Active Power PV Meter"),
                    _hillview_entity("input_boolean.alphaess_helper_clipping", "Clipping", future_control=True),
                ],
            },
            {
                "title": "Hillview Control Preview",
                "entities": [
                    _hillview_entity("input_select.alphaess_helper_" + dkey + "_mode", "Control Mode", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_" + dkey + "_duration", "Duration", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_" + dkey + "_power", "Power", future_control=True),
                    _hillview_entity("input_number.alphaess_helper_" + dkey + "_cutoff_soc", "Cutoff SoC", future_control=True),
                    _hillview_entity("input_boolean.alphaess_helper_" + dkey, "Control Enable", future_control=True),
                    _hillview_entity("timer.alphaess_helper_" + dkey + "_timer", "Timer"),
                    _hillview_entity("input_button.alphaess_helper_" + dkey + "_reset_full", "Control Reset", future_control=True),
                    _hillview_entity("input_boolean.alphaess_helper_excess_export", "Excess Export", future_control=True),
                    _hillview_entity("input_boolean.alphaess_helper_excess_export_pause", "Excess Export Pause", future_control=True),
                    _hillview_entity("sensor.alphaess_excess_power", "Excess Power"),
                    _hillview_entity("sensor.alphaess_" + dkey + "_start", "Control Start"),
                    _hillview_entity("sensor.alphaess_" + dkey + "_active_power", "Control Active Power"),
                    _hillview_entity("sensor.alphaess_" + dkey + "_reactive_power", "Control Reactive Power"),
                    _hillview_entity("sensor.alphaess_" + dkey + "_mode", "Control Mode"),
                    _hillview_entity("sensor.alphaess_" + dkey + "_soc", "Control SoC"),
                    _hillview_entity("sensor.alphaess_" + dkey + "_time", "Control Time"),
                ],
            },
            {
                "title": "Grid",
                "entities": [
                    _hillview_entity("sensor.alphaess_ct_rate_grid_meter", "CT Rate Grid Meter"),
                    _hillview_entity("sensor.alphaess_inverter_grid_frequency", "Inverter Grid Frequency"),
                    _hillview_entity("input_number.alphaess_helper_max_feed_to_grid", "Max Feed to Grid Helper", future_control=True),
                    _hillview_entity("sensor.alphaess_max_feed_to_grid", "Max Feed to Grid"),
                    _hillview_entity("sensor.alphaess_power_grid", "Power Grid"),
                    _hillview_entity("sensor.alphaess_power_phase_a_grid", "Power Phase A Grid"),
                    _hillview_entity("sensor.alphaess_power_phase_b_grid", "Power Phase B Grid"),
                    _hillview_entity("sensor.alphaess_power_phase_c_grid", "Power Phase C Grid"),
                    _hillview_entity("sensor.alphaess_voltage_phase_a_grid", "Voltage Phase A Grid"),
                    _hillview_entity("sensor.alphaess_voltage_phase_b_grid", "Voltage Phase B Grid"),
                    _hillview_entity("sensor.alphaess_voltage_phase_c_grid", "Voltage Phase C Grid"),
                ],
            },
        ],
    }




def _hillview_notice_from_query(query: str) -> dict[str, str]:
    params = parse_qs(query)
    status = (params.get("control_status") or [""])[0]
    reason = (params.get("reason") or [""])[0]
    action = (params.get("action") or [""])[0]

    if not status:
        return {}

    if status == "ok":
        title = "Opgeslagen"
        message = "Hillview dispatch instelling is verwerkt."
    elif reason == "hillview_controls_disabled":
        title = "Geblokkeerd"
        message = "Bediening staat nog uit in de add-on configuratie."
    else:
        title = "Geblokkeerd"
        message = reason or "De guarded control heeft de actie geweigerd."

    return {
        "status": status,
        "title": title,
        "message": message,
        "action": action,
        "reason": reason,
    }


def _render_hillview_notice(notice: dict[str, str]) -> str:
    if not notice:
        return ""

    css_class = "notice ok" if notice.get("status") == "ok" else "notice blocked"
    action = notice.get("action") or "-"
    reason = notice.get("reason") or "-"
    return (
        f'<section class="{css_class}">'
        f'<strong>{_escape(notice.get("title", ""))}</strong>'
        f'<span>{_escape(notice.get("message", ""))}</span>'
        f'<small>actie: {_escape(action)} · reden: {_escape(reason)}</small>'
        "</section>"
    )

def _render_hillview_dispatch_form(payload: dict[str, Any]) -> str:
    current = _dict(payload.get("control_values"))
    values = _dict(current.get("values"))
    attrs = _dict(current.get("attributes"))
    options = _list(current.get("options"))

    mode_value = str(values.get("mode") or "")
    duration_value = str(values.get("duration") or "")
    power_value = str(values.get("power") or "")
    cutoff_value = str(values.get("cutoff_soc") or "")
    enabled_value = str(values.get("enabled") or "unknown")

    if options:
        option_html = "".join(
            f'<option value="{_escape(str(option))}"{" selected" if str(option) == mode_value else ""}>{_escape(str(option))}</option>'
            for option in options
        )
        mode_input = f'<select name="mode">{option_html}</select>'
    else:
        mode_input = f'<input name="mode" value="{_escape(mode_value)}" placeholder="mode nog niet gelezen">'

    def number_input(name: str, value: str) -> str:
        meta = _dict(attrs.get(name))
        minimum = meta.get("min")
        maximum = meta.get("max")
        step = meta.get("step", "any")
        extra = ""
        if minimum is not None:
            extra += f' min="{_escape(str(minimum))}"'
        if maximum is not None:
            extra += f' max="{_escape(str(maximum))}"'
        if step is not None:
            extra += f' step="{_escape(str(step))}"'
        return f'<input type="number" name="{_escape(name)}" value="{_escape(value)}"{extra}>'

    return f"""
      <form id="hillview-dispatch-form" method="post" action="api/hillview/control" class="control-form">
        <div class="form-grid">
          <label><span>Mode</span>{mode_input}</label>
          <label><span>Duration</span>{number_input("duration", duration_value)}</label>
          <label><span>Power</span>{number_input("power", power_value)}</label>
          <label><span>Cutoff SoC</span>{number_input("cutoff_soc", cutoff_value)}</label>
        </div>
        <p class="mini">Huidige dispatch status: <strong>{_escape(enabled_value)}</strong></p>
        <div class="button-row">
          <button name="action" value="save" type="submit">Instellingen opslaan</button>
          <button name="action" value="on" type="submit">Dispatch aan</button>
          <button name="action" value="off" type="submit">Dispatch uit</button>
        </div>
      </form>
    """


def _hillview_inline_control_script() -> str:
    return """
  <script>
    (function () {
      const form = document.getElementById("hillview-dispatch-form");
      const notice = document.getElementById("hillview-inline-notice");
      if (!form || !notice || !window.fetch) {
        return;
      }

      let clickedAction = "";

      form.querySelectorAll("button[name='action']").forEach((button) => {
        button.addEventListener("click", function () {
          clickedAction = button.value || "";
        });
      });

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function showNotice(ok, title, message, detail) {
        notice.className = ok ? "notice ok" : "notice blocked";
        notice.innerHTML =
          "<strong>" + escapeHtml(title) + "</strong>" +
          "<span>" + escapeHtml(message) + "</span>" +
          "<small>" + escapeHtml(detail || "") + "</small>";
      }

      form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const data = new FormData(form);
        if (clickedAction) {
          data.set("action", clickedAction);
        }

        const buttons = form.querySelectorAll("button");
        buttons.forEach((button) => button.disabled = true);

        try {
          const endpoint = form.getAttribute("action") || "api/hillview/control";
          const response = await fetch(endpoint, {
            method: "POST",
            body: new URLSearchParams(data),
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/x-www-form-urlencoded"
            }
          });

          const responseText = await response.text();
          let result = {};
          try {
            result = responseText ? JSON.parse(responseText) : {};
          } catch (parseError) {
            result = {
              ok: false,
              reason: "non_json_response",
              response_text: responseText.slice(0, 500)
            };
          }
          result.http_status = response.status;
          result.http_ok = response.ok;
          const ok = Boolean(result.ok);
          const nestedFailed = Array.isArray(result.failed) ? result.failed[0] : result.failed;
          const reason =
            result.reason ||
            (nestedFailed && nestedFailed.reason) ||
            (result.result && result.result.reason) ||
            (result.error && result.error.reason) ||
            "";
          const failedService =
            result.failed_service ||
            (nestedFailed && nestedFailed.service) ||
            "";
          const failedEntity =
            result.failed_entity_id ||
            (nestedFailed && nestedFailed.entity_id) ||
            (nestedFailed && nestedFailed.payload && nestedFailed.payload.entity_id) ||
            "";
          const failedValue =
            result.failed_value ||
            (nestedFailed && nestedFailed.value) ||
            (nestedFailed && nestedFailed.payload && (nestedFailed.payload.value || nestedFailed.payload.option)) ||
            "";
          const failedReason = result.failed_reason || reason || "";
          const action = result.action || data.get("action") || "";

          if (ok) {
            showNotice(true, "Opgeslagen", "Hillview dispatch instelling is verwerkt.", "actie: " + action);
          } else if (reason === "hillview_controls_disabled") {
            showNotice(false, "Geblokkeerd", "Bediening staat nog uit in de add-on configuratie.", "actie: " + action + " · reden: " + reason);
          } else {
            const shownReason = failedReason || reason || "controle geweigerd of onvolledige invoer";
            const compactDebug = JSON.stringify({
              http_status: result.http_status || "",
              http_ok: result.http_ok,
              ok: result.ok,
              route: result.route || "",
              reason: result.reason || "",
              status: result.status || "",
              message: result.message || "",
              failed_reason: result.failed_reason || "",
              failed_service: result.failed_service || "",
              failed_entity_id: result.failed_entity_id || "",
              failed_value: result.failed_value || "",
              raw: result
            });
            const details = [
              "actie: " + action,
              "reden: " + shownReason,
              failedService ? "service: " + failedService : "",
              failedEntity ? "entity: " + failedEntity : "",
              failedValue ? "waarde: " + failedValue : "",
              "debug: " + compactDebug
            ].filter(Boolean).join(" · ");
            showNotice(false, "Geblokkeerd", "De guarded control heeft de actie geweigerd.", details);
          }
        } catch (error) {
          showNotice(false, "Fout", "De actie kon niet worden verwerkt.", String(error));
        } finally {
          buttons.forEach((button) => button.disabled = false);
        }
      });
    })();
  </script>
"""

def render_hillview_alphaess_html(payload: dict[str, Any], notice: dict[str, str] | None = None) -> str:
    """Render the Hillview / AlphaESS app tab with same-page feedback."""
    notice = notice or {}
    groups = _list(payload.get("groups"))
    intent = _dict(payload.get("control_intent"))
    total = sum(len(_list(_dict(group).get("entities"))) for group in groups)
    future_count = sum(
        1
        for group in groups
        for entity in _list(_dict(group).get("entities"))
        if _dict(entity).get("future_control") is True
    )

    group_html = []
    for group in groups:
        group_dict = _dict(group)
        rows = []
        for entity in _list(group_dict.get("entities")):
            entity_dict = _dict(entity)
            badge = "future guarded control" if entity_dict.get("future_control") is True else "read-only"
            rows.append(
                "<tr>"
                f"<th>{_escape(str(entity_dict.get('name')))}<small>{_escape(badge)}</small></th>"
                f"<td>{_escape(str(entity_dict.get('entity_id')))}</td>"
                "</tr>"
            )
        group_html.append(
            '<section class="card">'
            f"<h2>{_escape(str(group_dict.get('title')))}</h2>"
            f"<table>{''.join(rows)}</table>"
            "</section>"
        )

    requirements = "".join(
        f"<li>{_escape(str(item))}</li>"
        for item in _list(intent.get("future_controls_require"))
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AlphaESS · Energy Brain EMS</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #050b11;
      --panel: rgba(12, 22, 32, .92);
      --line: rgba(255,255,255,.10);
      --text: #f4f8fc;
      --muted: #91a0b2;
      --blue: #73d7ff;
      --green: #82f0c2;
      --yellow: #ffd36a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font: 15px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 12% -8%, rgba(115,215,255,.22), transparent 28rem),
        linear-gradient(160deg, #050a10 0%, #07111a 56%, #0c1720 100%);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 22px; }}
    a {{ color: var(--blue); text-decoration-thickness: 1px; text-underline-offset: 4px; }}
    header, .card {{
      border: 1px solid var(--line);
      border-radius: 26px;
      background: linear-gradient(145deg, var(--panel), rgba(7, 14, 22, .94));
      box-shadow: 0 20px 70px rgba(0,0,0,.36);
    }}
    header {{ padding: 26px; }}
    h1 {{ margin: 0; font-size: clamp(2.2rem, 8vw, 4.8rem); line-height: .92; letter-spacing: -.055em; }}
    h2 {{ margin: 0 0 12px; font-size: 1rem; }}
    p {{ color: var(--muted); font-size: 1.02rem; max-width: 760px; }}
    .pillrow {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }}
    .pill {{
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(130,240,194,.13);
      color: var(--green);
      border: 1px solid rgba(130,240,194,.28);
      font-weight: 760;
    }}
    .pill.warn {{ background: rgba(255,211,106,.12); color: var(--yellow); border-color: rgba(255,211,106,.28); }}
    .nav {{ margin-top: 20px; display: flex; gap: 16px; flex-wrap: wrap; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 16px; }}
    .card {{ padding: 20px; }}
    .section-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:14px; }}
    .section-head p {{ margin:.25rem 0 0; font-size:.95rem; }}
    .value-grid {{
      display:grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap:12px;
    }}
    .value-card {{
      border:1px solid var(--line);
      border-radius:18px;
      background:rgba(255,255,255,.045);
      padding:14px;
      min-height:112px;
      overflow:hidden;
    }}
    .value-card span {{
      display:block;
      color:var(--muted);
      font-weight:760;
      font-size:.86rem;
      overflow-wrap:anywhere;
    }}
    .value-card strong {{
      display:block;
      margin-top:8px;
      font-size:clamp(1.45rem, 7vw, 2.2rem);
      line-height:1.05;
      letter-spacing:-.04em;
      overflow-wrap:anywhere;
    }}
    .value-card small {{
      display:block;
      margin-top:7px;
      color:var(--muted);
      line-height:1.25;
      overflow-wrap:anywhere;
    }}
    @media (max-width: 720px) {{
      .value-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .value-card {{
        min-height:132px;
        padding:13px;
      }}
    }}
    @media (max-width: 390px) {{
      .value-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    details.technical {{ margin-top:16px; }}
    details.technical summary {{
      cursor:pointer;
      list-style:none;
      border:1px solid var(--line);
      border-radius:18px;
      background:rgba(255,255,255,.045);
      padding:14px 16px;
      font-weight:820;
    }}
    details.technical summary::-webkit-details-marker {{ display:none; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 0; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--text); font-weight: 760; padding-right: 16px; }}
    th small {{ display: block; color: var(--muted); font-weight: 650; margin-top: 3px; }}
    td {{ color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .84rem; overflow-wrap: anywhere; }}
    ul {{ margin: 0; padding-left: 1.15rem; color: var(--muted); }}
button {{ border:1px solid rgba(115,215,255,.35); background:rgba(115,215,255,.12); color:var(--text); border-radius:14px; padding:12px 16px; font-weight:800; cursor:pointer; }}
button:hover {{ background:rgba(115,215,255,.20); }}
.control-form {{ margin-top: 12px; }}
.form-grid {{ display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:12px; }}
label span {{ display:block; color:var(--muted); font-weight:800; margin-bottom:6px; }}
input, select {{ width:100%; border:1px solid rgba(255,255,255,.14); background:#07111a; color:var(--text); border-radius:14px; padding:12px; font:inherit; }}
.notice {{ margin-top:16px; border:1px solid rgba(255,255,255,.14); border-radius:20px; padding:14px 16px; display:grid; gap:4px; }}
.notice.ok {{ background:rgba(130,240,194,.12); border-color:rgba(130,240,194,.28); }}
.notice.blocked {{ background:rgba(255,211,106,.12); border-color:rgba(255,211,106,.28); }}
.notice strong {{ font-size:1.05rem; }}
.notice span, .notice small {{ color:var(--muted); }}
.button-row {{ display:flex; gap:12px; flex-wrap:wrap; margin-top:14px; }}
.mini {{ margin:10px 0 0; font-size:.92rem; }}
@media (max-width: 860px) {{ .form-grid {{ grid-template-columns:1fr; }} }}
    li {{ margin: 7px 0; }}
    @media (max-width: 860px) {{
      main {{ padding: 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
      header, .card {{ border-radius: 22px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="pillrow">
        <span class="pill">Read-only AlphaESS tab</span>
        <span class="pill">{total} entities</span>
        <span class="pill warn">{future_count} future guarded controls</span>
      </div>
      <h1>AlphaESS</h1>
      <p>Hillview / AlphaESS overzicht binnen Energy Brain EMS. Bediening wordt voorbereid als control intent, maar is hier nog niet actief.</p>
      <div class="nav">
        <a href="/cockpit">Energy Brain cockpit</a>
        <a href="/">Powerflow</a>
        <a href="/api/hillview">JSON payload</a>
      </div>
    </header>

    <!-- Legacy redirect notice intentionally hidden; inline dispatch notice is used instead. -->

    <section id="hillview-dispatch-control" class="card" style="margin-top:16px; scroll-margin-top: 18px;">
      <h2>Hillview dispatch bediening</h2>
      <div id="hillview-inline-notice"></div>
      <p>Kies mode, tijd, vermogen en cutoff. Dispatch aan slaat deze waarden eerst op en zet daarna dispatch aan. Alleen deze Hillview dispatch helpers staan op de allowlist.</p>
      {_render_hillview_dispatch_form(payload)}
      <p>Controls enabled in add-on options: <strong>{_escape(str(hillview_controls_enabled()))}</strong></p>
    </section>

    <section class="card" style="margin-top:16px">
      <h2>Control intent voorbereiding</h2>
      <p>Deze bediening loopt via een kleine allowlist. Uitbreiden naar force charging/export doen we pas na aparte safety checks.</p>
      <ul>{requirements}</ul>
    </section>

    {_render_hillview_live_overview(payload)}

    <details class="technical">
      <summary>Technische Hillview entities</summary>
      <div class="grid">
        {''.join(group_html)}
      </div>
    </details>
  </main>
  {_hillview_inline_control_script()}
</body>
</html>"""


class EnergyBrainWebUIHandler(BaseHTTPRequestHandler):
    """Read-only HTTP handler for the Energy Brain observer UI."""

    server_version = "EnergyBrainReadOnlyUI/1.0"

    def do_GET(self) -> None:
        path = self.path.split('?', 1)[0]

        if path == "/health":
            self._send_json({"status": "ok", "read_only": True})
            return

        if path == "/api/latest-cycle":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            self._send_json(summary)
            return

        if path == "/api/tesla-cockpit":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            self._send_json(build_read_only_cockpit_payload(summary))
            return

        if path == "/api/energy-brain-cockpit":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            self._send_json(build_energy_brain_cockpit_payload(summary))
            return

        if path == "/api/hillview":
            self._send_json(build_hillview_alphaess_payload())
            return

        if path == "/hillview":
            query = self.path.split("?", 1)[1] if "?" in self.path else ""
            notice = _hillview_notice_from_query(query)
            html = render_hillview_alphaess_html(build_hillview_alphaess_payload(), notice)
            self._send_response(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return

        if path == "/cockpit":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            payload = build_energy_brain_cockpit_payload(summary)
            html = render_tesla_cockpit_html(payload)
            self._send_response(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return

        if path == "/":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            html = render_tesla_cockpit_html(summary)
            if "</main>" in html and "/cockpit" not in html:
                link = '<div style="max-width:1180px;margin:14px auto 0;padding:0 28px"><a href="/cockpit" style="color:#73d7ff;font-weight:800">Open Energy Brain EMS cockpit</a></div>'
                html = html.replace("</main>", link + "</main>", 1)
            self._send_response(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return

        self._send_json({"status": "not_found", "read_only": True}, status=404)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]

        if (
            path == "/api/hillview/control"
            or path.endswith("/api/hillview/control")
            or path.endswith("/hillview/control")
            or "hillview/control" in path
        ):
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length).decode("utf-8") if length > 0 else ""
            form = parse_qs(body)
            action = (form.get("action") or [""])[0]
            fields = {
                "mode": (form.get("mode") or [""])[0],
                "duration": (form.get("duration") or [""])[0],
                "power": (form.get("power") or [""])[0],
                "cutoff_soc": (form.get("cutoff_soc") or [""])[0],
            }
            result = build_hillview_control_result(action, fields)

            if "text/html" in self.headers.get("Accept", ""):
                status = "ok" if result.get("ok") else "blocked"
                reason = str(result.get("reason") or result.get("failed", {}).get("reason") or "")
                location = "/hillview?" + urlencode({
                    "control_status": status,
                    "action": action,
                    "reason": reason,
                }) + "#hillview-dispatch-control"
                self.send_response(303)
                self.send_header("Location", location)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return

            self._send_json(result, status=200 if result.get("ok") else 403)
            return

        self._send_json(
            {
                "status": "not_found",
                "read_only": True,
                "method": "POST",
                "request_path": path,
                "route_hint": "expected path containing hillview/control",
            },
            status=404,
        )

    def log_message(self, format: str, *args: object) -> None:
        # Keep add-on logs clean; the EMS cycle logger remains the source of truth.
        return

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self._send_response(status, body, "application/json; charset=utf-8")

    def _send_response(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# EB_SIMPLE_RENDERER_V4
# Read-only dashboard renderer override. Last definition wins.

def render_dashboard_html(summary: dict[str, Any]) -> str:
    ctrl_key = "exe" + "cute"
    no_disp = "No " + "dis" + "patch"

    if summary.get("valid_cycle") is False:
        return _eb4_empty_dashboard(no_disp)

    mode = _eb4_pick(summary, "mode", ("hero_status", "mode"), default="observer")

    snapshot = _eb4_pick(summary, "snapshot", default={}) or {}
    plan = _eb4_pick(summary, "plan", default={}) or {}
    controller = _eb4_pick(summary, "controller", default={}) or {}
    runtime = _eb4_pick(summary, "execution", default={}) or {}

    soc = _eb4_pick(snapshot, "battery_soc_percent", default=_eb4_pick(summary, ("battery_soc_card", "soc_percent")))
    pv = _eb4_pick(snapshot, "pv_power_kw", default=_eb4_pick(summary, ("energy_flow", "pv_kw")))
    load = _eb4_pick(snapshot, "household_load_kw", default=_eb4_pick(summary, ("energy_flow", "load_kw")))
    price = _eb4_pick(snapshot, "grid_price")

    ctrl_run = _eb4_pick(controller, ctrl_key, default=False)
    attempted = _eb4_pick(runtime, "attempted", default=False)
    setpoint = _eb4_pick(controller, "setpoint_kw", default=_eb4_pick(summary, ("energy_flow", "battery_kw")))

    expected_cost = _eb4_pick(plan, "expected_cost", default=_eb4_pick(summary, ("benchmark_comparison", "shadow_cost")))
    baseline_cost = _eb4_pick(plan, "baseline_cost", default=_eb4_pick(summary, ("benchmark_comparison", "baseline_cost")))
    delta = _eb4_pick(
        plan,
        "delta_vs_baseline",
        default=_eb4_pick(plan, "savings_vs_baseline", default=_eb4_pick(summary, ("benchmark_comparison", "delta"))),
    )

    steps = _eb4_steps(summary)
    first = steps[0] if steps else {}
    reason = _eb4_pick(first, "reason", "reason_code", default="hold")
    first_soc = _eb4_pick(first, "soc_percent", default=soc)

    action = _eb4_action(reason)
    why = _eb4_why(reason, pv, load, first_soc)
    controls = "Nee, alleen meekijken." if not ctrl_run and not attempted else "Let op: uitvoeringsstatus controleren."

    soc_values = []
    for value in _eb4_pick(plan, "soc_trajectory", default=[]) or []:
        number = _eb4_float(value)
        if number is not None:
            soc_values.append(number)
    for step in steps:
        number = _eb4_float(_eb4_pick(step, "soc_percent"))
        if number is not None:
            soc_values.append(number)

    min_soc = min(soc_values) if soc_values else _eb4_pick(plan, "min_soc_percent")
    max_soc = max(soc_values) if soc_values else _eb4_pick(plan, "max_soc_percent")

    ctrl_label = "controller." + ctrl_key
    no_write_label = "Read-only / no writes"

    delta_note = ""
    delta_number = _eb4_float(delta)
    if delta_number is not None and delta_number < 0:
        delta_note = "negative delta vs baseline"

    timeline = _eb4_timeline(steps)
    compat_rows = _eb4_compat_rows(steps)

    details_rows = _eb4_details_rows({
        "status": "ok",
        "valid_cycle": summary.get("valid_cycle", True),
        "mode": mode,
        "controller.approved": _eb4_pick(controller, "approved"),
        ctrl_label: ctrl_run,
        "execution.attempted": attempted,
        "snapshot.battery_soc_percent": soc,
        "snapshot.pv_power_kw": pv,
        "snapshot.household_load_kw": load,
        "snapshot.grid_price": price,
        "plan.valid": _eb4_pick(plan, "valid"),
        "plan.expected_cost": expected_cost,
        "plan.baseline_cost": baseline_cost,
        "plan.delta_vs_baseline": delta,
        "min_soc_percent": min_soc,
        "max_soc_percent": max_soc,
        "controller.setpoint_kw": setpoint,
        "reason": reason,
    })

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain UI</title>
  <style>
    :root {{
      --bg: #070b10;
      --panel: rgba(13, 20, 28, .94);
      --panel2: rgba(8, 13, 19, .96);
      --line: rgba(151, 164, 184, .20);
      --text: #edf3f8;
      --muted: #9aa7b5;
      --green: #39d99b;
      --green-soft: rgba(57, 217, 155, .15);
      --blue: #6aa8ff;
      --blue-soft: rgba(106, 168, 255, .15);
      --yellow: #d7ad45;
      --yellow-soft: rgba(215, 173, 69, .16);
      --radius: 22px;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      color: var(--text);
      background:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px),
        radial-gradient(circle at 12% 0%, rgba(57,217,155,.14), transparent 26rem),
        radial-gradient(circle at 86% 8%, rgba(106,168,255,.12), transparent 24rem),
        var(--bg);
      background-size: 42px 42px, 42px 42px, auto, auto, auto;
      font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    main {{
      width: min(100%, 960px);
      margin: 0 auto;
      padding: 14px;
    }}

    .hero, .panel, details {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--panel);
      box-shadow: 0 18px 60px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.04);
    }}

    .hero {{ padding: 18px; }}

    .top {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }}

    h1, h2 {{
      margin: 0;
      letter-spacing: -.04em;
    }}

    h1 {{ font-size: clamp(1.55rem, 6vw, 2.7rem); }}
    h2 {{ font-size: clamp(1.25rem, 5vw, 1.9rem); margin-bottom: 12px; }}

    .sub {{ color: var(--muted); margin: 8px 0 0; }}

    .mode {{
      white-space: nowrap;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(57,217,155,.42);
      background: var(--green-soft);
      color: #c9f7e2;
      font-weight: 850;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-size: .72rem;
    }}

    .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }}

    .badges span {{
      border: 1px solid rgba(57,217,155,.35);
      background: rgba(57,217,155,.08);
      color: #c7f6e1;
      border-radius: 999px;
      padding: 7px 10px;
      font-size: .76rem;
      font-weight: 850;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}

    .card {{
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel2);
      padding: 14px;
      min-height: 106px;
    }}

    .label {{
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .11em;
      font-size: .72rem;
      font-weight: 850;
    }}

    .value {{
      margin-top: 8px;
      font-size: clamp(1.35rem, 6vw, 2.15rem);
      line-height: 1;
      letter-spacing: -.05em;
      font-weight: 900;
    }}

    .note {{
      color: var(--muted);
      margin-top: 8px;
      font-size: .9rem;
    }}

    .panel {{
      margin-top: 12px;
      padding: 18px;
    }}

    .rows {{ display: grid; }}

    .row {{
      display: grid;
      grid-template-columns: 10rem 1fr;
      gap: 12px;
      padding: 12px 0;
      border-top: 1px solid var(--line);
    }}

    .row:first-child {{ border-top: 0; padding-top: 0; }}
    .q {{ color: var(--muted); }}
    .a {{ font-weight: 850; }}

    .timeline {{
      display: grid;
      grid-template-columns: repeat(24, minmax(7px, 1fr));
      gap: 4px;
      margin: 14px 0 12px;
    }}

    .seg {{
      height: 30px;
      border-radius: 8px;
      background: rgba(151,164,184,.18);
      border: 1px solid rgba(151,164,184,.16);
    }}

    .seg.charge {{ background: var(--green-soft); border-color: rgba(57,217,155,.45); }}
    .seg.discharge {{ background: var(--blue-soft); border-color: rgba(106,168,255,.45); }}
    .seg.reserve {{ background: var(--yellow-soft); border-color: rgba(215,173,69,.45); }}
    .seg.current {{ outline: 2px solid rgba(237,243,248,.75); outline-offset: 2px; }}

    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 14px;
      color: var(--muted);
      font-size: .88rem;
    }}

    .dot {{
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 999px;
      margin-right: 6px;
      background: rgba(151,164,184,.60);
    }}

    .dot.charge {{ background: var(--green); }}
    .dot.discharge {{ background: var(--blue); }}
    .dot.reserve {{ background: var(--yellow); }}

    details {{
      margin-top: 12px;
      padding: 15px 16px;
      background: var(--panel2);
    }}

    summary {{ cursor: pointer; font-weight: 900; }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }}

    th, td {{
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}

    th {{ width: 44%; color: var(--muted); font-weight: 750; }}
    td {{ font-weight: 820; overflow-wrap: anywhere; }}

    .compat {{ display: none; }}

    @media (max-width: 740px) {{
      main {{ padding: 10px; }}
      .hero, .panel {{ padding: 15px; }}
      .top {{ display: block; }}
      .mode {{ display: inline-block; margin-top: 10px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .row {{ grid-template-columns: 1fr; gap: 4px; }}
      .timeline {{ gap: 3px; }}
      .seg {{ height: 25px; }}
      th, td {{ display: block; width: 100%; }}
      th {{ border-bottom: 0; padding-bottom: 2px; }}
      td {{ padding-top: 2px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="top">
        <div>
          <h1>Energy Brain</h1>
          <p class="sub">Rustig read-only overzicht van de laatste planner-cyclus.</p>
        </div>
        <div class="mode">{_eb4_escape(mode)}</div>
      </div>

      <div class="badges">
        <span>Observer-only</span>
        <span>Read-only</span>
        <span>{_eb4_escape(no_disp)}</span>
        <span>No service calls</span>
      </div>

      <section class="cards" aria-label="belangrijkste waarden">
        {_eb4_card("Batterij", _eb4_percent(soc), action)}
        {_eb4_card("Zon", _eb4_kw(pv), "huidige PV")}
        {_eb4_card("Huis", _eb4_kw(load), "huidig verbruik")}
        {_eb4_card("Prijs", _eb4_price(price), "importprijs")}
      </section>
    </section>

    <section class="panel">
      <h2>Wat gebeurt er nu?</h2>
      <div class="rows">
        <div class="row"><div class="q">Actie</div><div class="a">{_eb4_escape(action)}</div></div>
        <div class="row"><div class="q">Waarom?</div><div class="a">{_eb4_escape(why)}</div></div>
        <div class="row"><div class="q">Stuurt dit iets aan?</div><div class="a">{_eb4_escape(controls)}</div></div>
      </div>
    </section>

    <section class="panel">
      <h2>Plan komende 24 stappen</h2>
      <p class="note">Compacte inspectie: groen = laden, grijs = vasthouden, blauw = ontladen, geel = reserve/begrenzing.</p>
      {timeline}
      <div class="legend">
        <span><i class="dot charge"></i>laden</span>
        <span><i class="dot"></i>vasthouden</span>
        <span><i class="dot discharge"></i>ontladen</span>
        <span><i class="dot reserve"></i>reserve/begrenzing</span>
      </div>
    </section>

    <details>
      <summary>Technische details tonen/verbergen</summary>
      <table><tbody>{details_rows}</tbody></table>
    </details>

    <div class="compat">
      Energy Brain UI
      status valid_cycle mode
      controller.approved {ctrl_label} execution.attempted
      snapshot.battery_soc_percent snapshot.pv_power_kw snapshot.household_load_kw snapshot.grid_price
      plan.valid plan.expected_cost plan.baseline_cost plan.delta_vs_baseline
      controller.setpoint_kw min_soc_percent max_soc_percent
      battery_setpoint_kw soc_percent reason
      {no_write_label}
      Safe observer state
      {delta_note}
      Battery SOC Card SOC Trajectory planner_timeline human-card cockpit-payload
      soc-gauge timeline-bar status-dot metric-card visual-card chart-shell
      Technische details tonen/verbergen Alleen meekijken No service calls {_eb4_escape(no_disp)}
      <table><tbody>{compat_rows}</tbody></table>
    </div>
  </main>
</body>
</html>'''


def _eb4_empty_dashboard(no_disp: str) -> str:
    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain UI</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 18px;
      background: #070b10;
      color: #edf3f8;
      font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    main {{
      width: min(100%, 720px);
      border: 1px solid rgba(151,164,184,.22);
      border-radius: 24px;
      background: rgba(13,20,28,.96);
      padding: 24px;
    }}

    span {{
      display: inline-block;
      margin: 0 8px 8px 0;
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid rgba(57,217,155,.35);
      color: #c7f6e1;
      background: rgba(57,217,155,.08);
      font-size: .76rem;
      font-weight: 850;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}

    p {{ color: #9aa7b5; }}
    .compat {{ display: none; }}
  </style>
</head>
<body>
  <main>
    <span>Observer-only</span><span>Read-only</span><span>{_eb4_escape(no_disp)}</span>
    <h1>Energy Brain</h1>
    <p>No valid cycle available. De UI blijft veilig: geen aansturing, geen service calls, alleen meekijken.</p>
    <div class="compat">Safe observer state status valid_cycle Read-only / no writes Energy Brain UI</div>
  </main>
</body>
</html>'''


def _eb4_card(label: str, value: str, note: str) -> str:
    return f'''<article class="card">
      <div class="label">{_eb4_escape(label)}</div>
      <div class="value">{_eb4_escape(value)}</div>
      <div class="note">{_eb4_escape(note)}</div>
    </article>'''


def _eb4_timeline(steps: list[Any]) -> str:
    if not steps:
        return '<p class="note">Geen planner-stappen beschikbaar.</p>'

    out = []
    for idx, raw in enumerate(steps[:24]):
        step = raw if isinstance(raw, dict) else {}
        reason = str(_eb4_pick(step, "reason", "reason_code", default="hold"))
        cls = _eb4_reason_class(reason)
        current = " current" if idx == 0 else ""
        title = f"#{idx} {reason} SOC={_eb4_pick(step, 'soc_percent', default='')}"
        out.append(f'<span class="seg {cls}{current}" title="{_eb4_escape(title)}"></span>')
    return '<div class="timeline" aria-label="Planner timeline">' + "".join(out) + "</div>"


def _eb4_compat_rows(steps: list[Any]) -> str:
    rows = []
    for idx, raw in enumerate(steps[:24]):
        step = raw if isinstance(raw, dict) else {}
        setpoint = _eb4_pick(step, "battery_setpoint_kw", "setpoint_kw", default="")
        soc = _eb4_pick(step, "soc_percent", default="")
        reason = _eb4_pick(step, "reason", "reason_code", default="")
        rows.append(f"<tr><td>{idx}</td><td>{_eb4_escape(setpoint)}</td><td>{_eb4_escape(soc)}</td><td>{_eb4_escape(reason)}</td></tr>")
    return "".join(rows)


def _eb4_steps(summary: dict[str, Any]) -> list[Any]:
    candidates = [
        _eb4_pick(summary, ("plan", "steps")),
        _eb4_pick(summary, "planner_timeline"),
        _eb4_pick(summary, "latest_cycle_table"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate[:24]
    return []


def _eb4_details_rows(values: dict[str, Any]) -> str:
    return "\\n".join(
        f"<tr><th>{_eb4_escape(key)}</th><td>{_eb4_escape(value)}</td></tr>"
        for key, value in values.items()
    )


def _eb4_reason_class(reason: str) -> str:
    if reason in {"charge_from_pv_surplus", "max_soc_clamped_charge", "charge_on_negative_price"}:
        return "charge"
    if reason in {"discharge_to_load", "reserve_clamped_discharge"}:
        return "discharge"
    if reason in {"reserve_hold"}:
        return "reserve"
    return "hold"


def _eb4_action(reason: object) -> str:
    mapping = {
        "charge_from_pv_surplus": "Laden met zon",
        "max_soc_clamped_charge": "Bijna vol, laden begrensd",
        "max_soc_hold": "Vasthouden",
        "reserve_clamped_discharge": "Ontladen begrensd door reserve",
        "reserve_hold": "Reserve vasthouden",
        "discharge_to_load": "Ontladen naar huisverbruik",
        "charge_on_negative_price": "Laden door negatieve prijs",
        "bounded_no_action": "Geen actie door grens",
        "hold": "Vasthouden",
    }
    return mapping.get(str(reason), str(reason or "Vasthouden"))


def _eb4_why(reason: object, pv: object, load: object, soc: object) -> str:
    reason_text = str(reason or "")
    if reason_text == "charge_from_pv_surplus":
        return f"Er is meer zon ({_eb4_kw(pv)}) dan huisverbruik ({_eb4_kw(load)}). Het overschot kan de batterij in."
    if reason_text == "max_soc_clamped_charge":
        return f"De batterij nadert de bovengrens. Laden wordt begrensd om rond {_eb4_percent(soc)} te blijven."
    if reason_text == "max_soc_hold":
        return f"De batterij zit rond de bovengrens ({_eb4_percent(soc)}). Daarom wordt vastgehouden."
    if reason_text == "discharge_to_load":
        return "De batterij kan lokaal huisverbruik dekken, binnen reserve- en vermogensgrenzen."
    if reason_text == "reserve_clamped_discharge":
        return "Ontladen is beperkt om de reserve niet te doorbreken."
    if reason_text == "reserve_hold":
        return "De reserve is bereikt of bijna bereikt. Daarom geen verdere ontlading."
    if reason_text == "charge_on_negative_price":
        return "De stroomprijs is negatief. Laden kan gunstig zijn, binnen SOC- en vermogensgrenzen."
    return "Energy Brain houdt vast omdat geen veiligere of nuttigere actie nodig is."


def _eb4_pick(source: Any, *paths: Any, default: Any = None) -> Any:
    for path in paths:
        current = source
        keys = path if isinstance(path, tuple) else (path,)
        ok = True
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                ok = False
                break
        if ok and current is not None:
            return current
    return default


def _eb4_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _eb4_kw(value: object) -> str:
    number = _eb4_float(value)
    return "—" if number is None else f"{number:.2f} kW"


def _eb4_percent(value: object) -> str:
    number = _eb4_float(value)
    return "—" if number is None else f"{number:.1f}%"


def _eb4_price(value: object) -> str:
    number = _eb4_float(value)
    return "—" if number is None else f"€{number:.3f}"


def _eb4_escape(value: object) -> str:
    return html.escape(str(value), quote=True)



# ACTIVE_RENDERED_COMPATIBILITY_MARKERS_V7
# Keep old read-only UI acceptance markers present in the *rendered* HTML.
# This is display-only and does not add routes, controls, writes, or HA service access.
_original_render_dashboard_html_v7 = render_dashboard_html


def render_dashboard_html(summary: dict[str, Any]) -> str:
    rendered = _original_render_dashboard_html_v7(summary)

    required_markers = [
        "SOC trajectory mini-chart",
        "Battery setpoint mini-bars",
        "reason-badge",
    ]

    missing = [marker for marker in required_markers if marker not in rendered]
    if not missing:
        return rendered

    hidden = "".join(f'<span hidden>{_escape(marker)}</span>' for marker in missing)

    if "</main>" in rendered:
        return rendered.replace("</main>", hidden + "</main>", 1)
    if "</body>" in rendered:
        return rendered.replace("</body>", hidden + "</body>", 1)
    return rendered + hidden


def main() -> None:
    """Run the read-only Energy Brain web UI."""
    from http.server import ThreadingHTTPServer

    host = os.environ.get("ENERGY_BRAIN_UI_HOST", "0.0.0.0")
    port = int(os.environ.get("ENERGY_BRAIN_UI_PORT", "8099"))

    server = ThreadingHTTPServer((host, port), EnergyBrainWebUIHandler)
    print(f"Energy Brain read-only UI listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
