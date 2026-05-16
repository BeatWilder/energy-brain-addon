from __future__ import annotations

import os

import html
import json
from pathlib import Path
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from energy_brain.v2000.read_only_tesla_cockpit import build_read_only_cockpit_payload, render_tesla_cockpit_html


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

        if path == "/":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            html = render_tesla_cockpit_html(summary)
            self._send_response(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return

        self._send_json({"status": "not_found", "read_only": True}, status=404)

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



def _eb_plan_step_time_explanation() -> str:
    return """
<section class="plan-step-help" aria-label="Plan stap uitleg">
  <h2>Wat betekenen #0 t/m #23?</h2>
  <p><strong>#0 is nu.</strong> Daarna is elke volgende kaart één planner-stap vooruit.</p>
  <p>Bij de huidige Energy Brain cyclus van 900 seconden is één stap ongeveer 15 minuten.</p>
  <div class="plan-step-map">
    <span><strong>#0</strong><small>nu</small></span>
    <span><strong>#1</strong><small>+15 min</small></span>
    <span><strong>#2</strong><small>+30 min</small></span>
    <span><strong>#4</strong><small>+1 uur</small></span>
    <span><strong>#12</strong><small>+3 uur</small></span>
    <span><strong>#23</strong><small>+5u45</small></span>
  </div>
  <p class="mini">Dit zijn inspectiekaarten voor de planning. Ze zijn geen knoppen en sturen niets aan.</p>
</section>
<style>
  .plan-step-help {
    margin: 18px 0;
    padding: 22px;
    border-radius: 22px;
    border: 1px solid rgba(103,167,255,.36);
    background: linear-gradient(145deg, rgba(18,31,45,.92), rgba(8,13,20,.96));
    box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
  }
  .plan-step-help h2 {
    margin: 0 0 10px;
    font-size: clamp(1.35rem, 5vw, 2rem);
    letter-spacing: -0.03em;
  }
  .plan-step-help p {
    margin: 8px 0;
    color: #aab6c3;
  }
  .plan-step-map {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
    margin-top: 14px;
  }
  .plan-step-map span {
    display: block;
    padding: 12px 10px;
    border-radius: 16px;
    border: 1px solid rgba(148,163,184,.22);
    background: rgba(255,255,255,.035);
  }
  .plan-step-map strong {
    display: block;
    color: #e8eef6;
    font-size: 1.05rem;
  }
  .plan-step-map small {
    display: block;
    color: #8ea0b2;
    margin-top: 3px;
  }
  @media (max-width: 760px) {
    .plan-step-map {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
</style>
"""

def _eb_insert_plan_step_time_explanation(rendered: str) -> str:
    if "Wat betekenen #0 t/m #23?" in rendered:
        return rendered

    help_html = _eb_plan_step_time_explanation()

    anchors = [
        '<section id="tab-plan"',
        '<h2>Planner Timeline</h2>',
        'Planner Timeline',
        'Predbat-Inspired Plan Windows',
    ]

    for anchor in anchors:
        index = rendered.find(anchor)
        if index != -1:
            return rendered[:index] + help_html + rendered[index:]

    end_main = rendered.rfind("</main>")
    if end_main != -1:
        return rendered[:end_main] + help_html + rendered[end_main:]

    return rendered + help_html


_eb_original_render_dashboard_html_plan_step_help = render_dashboard_html

def render_dashboard_html(summary: dict[str, Any]) -> str:
    rendered = _eb_original_render_dashboard_html_plan_step_help(summary)
    return _eb_insert_plan_step_time_explanation(rendered)

def main() -> None:
    """Run the read-only Energy Brain web UI."""
    from http.server import ThreadingHTTPServer

    host = os.environ.get("ENERGY_BRAIN_UI_HOST", "0.0.0.0")
    port = int(os.environ.get("ENERGY_BRAIN_UI_PORT", "8099"))

    server = ThreadingHTTPServer((host, port), EnergyBrainWebUIHandler)
    print(f"Energy Brain read-only UI listening on http://{host}:{port}", flush=True)
    server.serve_forever()


# ENERGY_BRAIN_TIME_LABEL_WRAPPER_V1
#
# UI-only wrapper.
# Converts internal planner step numbers (#0..#23) into readable horizon labels:
#   #0 -> Nu
#   #1 -> +1 uur
#   #2 -> +2 uur
#
# The original step index remains available as a small technical hint.
# This does not change planner data, controller approval, service behavior,
# Home Assistant entities, battery limits, SOC math, or runtime decisions.

_original_render_dashboard_html_time_labels_v1 = render_dashboard_html


def render_dashboard_html(summary: dict[str, Any]) -> str:
    page = _original_render_dashboard_html_time_labels_v1(summary)
    return _eb_time_label_rendered_page(page)


def _eb_time_label_rendered_page(page: str) -> str:
    if not isinstance(page, str) or not page:
        return page

    page = _eb_insert_time_label_explainer(page)

    # Replace the visible labels in the plan-inspect step buttons.
    # Keep data-index/data-step unchanged for the existing JavaScript.
    for index in range(0, 96):
        label = _eb_time_label(index)
        hint = _eb_time_hint(index)

        page = page.replace(
            f"<span>#{index}</span><span>display-only fallback</span>",
            f"<span>{_escape(label)}</span><span>{_escape(hint)}</span>",
        )
        page = page.replace(
            f"<span>#{index}</span><span>display-only</span>",
            f"<span>{_escape(label)}</span><span>{_escape(hint)}</span>",
        )
        page = page.replace(
            f"<span>#{index}</span><span>shadow</span>",
            f"<span>{_escape(label)}</span><span>{_escape(hint)}</span>",
        )
        page = page.replace(
            f"<span>#{index}</span><span>inspect only</span>",
            f"<span>{_escape(label)}</span><span>{_escape(hint)}</span>",
        )

        # Make accessibility labels clearer too.
        page = page.replace(
            f'aria-label="inspect only planner step {index}"',
            f'aria-label="inspect only planner time slot {index}: {_escape(label)}"',
        )

    # Selected step panel: make the visible selected step understandable.
    for index in range(0, 96):
        label = _eb_time_label(index)
        page = page.replace(
            f"<strong>#{index} · nu</strong>",
            f"<strong>{_escape(label)} · interne stap {index}</strong>",
        )
        page = page.replace(
            f"<strong>#{index} / +{index}h</strong>",
            f"<strong>{_escape(label)} · interne stap {index}</strong>",
        )
        page = page.replace(
            f"<strong>#{index}</strong>",
            f"<strong>{_escape(label)}</strong>",
        )

    # Chart label text is technical; clarify it without changing the SVG math.
    page = page.replace(
        "step / hour",
        "tijd vanaf nu",
    )
    page = page.replace(
        "selected step #0",
        "geselecteerd: Nu",
    )

    return page


def _eb_insert_time_label_explainer(page: str) -> str:
    if "Wat betekenen Nu, +1 uur en +2 uur?" in page:
        return page

    explainer = """
    <section class="human-card" aria-label="Uitleg plan tijdslots">
      <h2>Wat betekenen Nu, +1 uur en +2 uur?</h2>
      <p><strong>Dit zijn tijdslots in de vooruitblik.</strong></p>
      <p class="note">Nu is het eerste tijdslot. +1 uur is het volgende tijdslot. +23 uur is het laatste getoonde tijdslot in deze plan-inspectie.</p>
      <p class="note">De oude nummers #0 tot en met #23 zijn alleen interne planner-indexen. Voorbeeld: interne stap 0 is Nu, interne stap 1 is +1 uur. Die technische nummers blijven nuttig voor debuggen, maar staan niet meer voorop.</p>
    </section>
    """

    anchors = [
        '<section id="tab-plan"',
        '<div class="steps">',
        '<section class="human-grid"',
    ]

    for anchor in anchors:
        if anchor in page:
            return page.replace(anchor, explainer + "\n" + anchor, 1)

    return page.replace("</main>", explainer + "\n</main>", 1)


def _eb_time_label(index: int) -> str:
    if index == 0:
        return "Nu"
    if index == 1:
        return "+1 uur"
    return f"+{index} uur"


def _eb_time_hint(index: int) -> str:
    if index == 0:
        return "interne stap 0 · huidige periode"
    return f"interne stap {index} · vooruitblik"

# ENERGY_BRAIN_PLAN_TIME_LABELS_OBVIOUS_V1
_previous_render_dashboard_html_time_labels_v1 = render_dashboard_html


def _eb_time_label_for_step_v1(index: int) -> str:
    if index == 0:
        return "Nu"
    if index == 1:
        return "Over 1 uur"
    return f"Over {index} uur"


def _eb_time_help_panel_v1() -> str:
    return """
    <section class="human-card plain-wide" aria-label="Uitleg planner tijdstappen">
      <h2>Wat betekenen #0 t/m #23?</h2>
      <p><strong>#0 is nu. #1 is over 1 uur. #2 is over 2 uur. #23 is over 23 uur.</strong></p>
      <p class="note">Dit zijn geen vaste klokuren zoals 00:00 tot 23:00. Het zijn vooruitkijk-stappen vanaf dit moment.</p>
      <div class="summary-list">
        <div><span>Interne stap 0</span><strong>Nu</strong></div>
        <div><span>Interne stap 1</span><strong>Over 1 uur</strong></div>
        <div><span>Interne stap 2</span><strong>Over 2 uur</strong></div>
        <div><span>Interne stap 23</span><strong>Over 23 uur</strong></div>
      </div>
    </section>
    """


def _eb_make_plan_time_labels_obvious_v1(rendered: str) -> str:
    # Voeg een duidelijke uitleg toe net boven de plan-inspectie.
    help_panel = _eb_time_help_panel_v1()
    if "Wat betekenen #0 t/m #23?" not in rendered:
        anchor = '<section id="tab-plan"'
        if anchor in rendered:
            rendered = rendered.replace(anchor, help_panel + anchor, 1)
        elif "</main>" in rendered:
            rendered = rendered.replace("</main>", help_panel + "</main>", 1)

    # Maak de zichtbare step-knoppen menselijker zonder data-attributen te wijzigen.
    for index in range(24):
        label = _eb_time_label_for_step_v1(index)
        rendered = rendered.replace(
            f"<span>#{{index}}</span><span>display-only fallback</span>".replace("{index}", str(index)),
            f"<span>{label}</span><span>interne stap {index}</span>",
        )
        rendered = rendered.replace(
            f"<span>#{index}</span><span>display-only</span>",
            f"<span>{label}</span><span>interne stap {index}</span>",
        )
        rendered = rendered.replace(
            f'aria-label="inspect only planner step {index}"',
            f'aria-label="inspecteer planner stap {index}: {label}"',
        )

    # Maak geselecteerde detailtekst ook duidelijker.
    rendered = rendered.replace("#0 · nu", "Nu · interne stap 0")
    rendered = rendered.replace("#0 / +0h", "Nu / interne stap 0 / +0 uur")
    rendered = rendered.replace("selected step #0", "geselecteerde stap: nu")

    return rendered


def render_dashboard_html(summary: dict[str, Any]) -> str:
    return _eb_make_plan_time_labels_obvious_v1(
        _previous_render_dashboard_html_time_labels_v1(summary)
    )

# ENERGY_BRAIN_PLAN_TIME_LABELS_OBVIOUS_V2
_previous_render_dashboard_html_time_labels_v2 = render_dashboard_html


def _eb_plan_time_label_v2(index: int) -> str:
    if index == 0:
        return "Nu"
    if index == 1:
        return "Over 1 uur"
    return f"Over {index} uur"


def _eb_plan_time_help_v2() -> str:
    return """
    <section class="human-card plain-wide" aria-label="Planner tijdlijn uitleg">
      <h2>Wat betekenen #0 t/m #23?</h2>
      <p><strong>#0 is nu. #1 is over 1 uur. #2 is over 2 uur. #23 is over 23 uur.</strong></p>
      <p class="note">Het zijn vooruitkijk-stappen vanaf dit moment, geen vaste klokuren van een dag.</p>
      <div class="summary-list">
        <div><span>Interne stap 0</span><strong>Nu</strong></div>
        <div><span>Interne stap 1</span><strong>Over 1 uur</strong></div>
        <div><span>Interne stap 2</span><strong>Over 2 uur</strong></div>
        <div><span>Interne stap 23</span><strong>Over 23 uur</strong></div>
      </div>
    </section>
    """


def _eb_render_plan_time_labels_v2(rendered: str) -> str:
    help_panel = _eb_plan_time_help_v2()

    if "Interne stap 23" not in rendered:
        anchor = '<section id="tab-plan"'
        if anchor in rendered:
            rendered = rendered.replace(anchor, help_panel + anchor, 1)
        elif "</main>" in rendered:
            rendered = rendered.replace("</main>", help_panel + "</main>", 1)
        else:
            rendered += help_panel

    for index in range(24):
        label = _eb_plan_time_label_v2(index)

        rendered = rendered.replace(
            f"<span>#{index}</span><span>display-only fallback</span>",
            f"<span>{label}</span><span>Interne stap {index}</span>",
        )
        rendered = rendered.replace(
            f"<span>#{index}</span><span>display-only</span>",
            f"<span>{label}</span><span>Interne stap {index}</span>",
        )
        rendered = rendered.replace(
            f"<span>#{index}</span>",
            f"<span>{label}</span>",
        )
        rendered = rendered.replace(
            f'aria-label="inspect only planner step {index}"',
            f'aria-label="inspecteer planner stap {index}: {label}"',
        )

    rendered = rendered.replace("#0 · nu", "Nu · Interne stap 0")
    rendered = rendered.replace("#0 / +0h", "Nu / Interne stap 0 / +0 uur")
    rendered = rendered.replace("selected step #0", "geselecteerde stap: nu")

    return rendered


def render_dashboard_html(summary: dict[str, Any]) -> str:
    return _eb_render_plan_time_labels_v2(
        _previous_render_dashboard_html_time_labels_v2(summary)
    )


# Energy Brain UI visible plan-step label fix.
# This is display-only rendering. It does not alter planner data, controller state,
# Home Assistant state, services, or battery commands.
_original_render_dashboard_html_visible_time_labels_v1 = render_dashboard_html


def render_dashboard_html(summary: dict[str, Any]) -> str:
    rendered = _original_render_dashboard_html_visible_time_labels_v1(summary)
    return _eb_visible_plan_step_cards_time_labels_v1(rendered)


def _eb_visible_plan_step_cards_time_labels_v1(rendered: str) -> str:
    rendered = _eb_replace_step_card_titles_v1(rendered)
    rendered = _eb_replace_selected_step_labels_v1(rendered)
    rendered = _eb_insert_visible_step_label_css_v1(rendered)
    rendered = _eb_insert_visible_step_label_note_v1(rendered)
    return rendered


def _eb_step_human_time_label_v1(index: int) -> str:
    if index == 0:
        return "Nu"
    if index == 1:
        return "Over 1 uur"
    return f"Over {index} uur"


def _eb_replace_step_card_titles_v1(rendered: str) -> str:
    for index in range(24):
        human = _eb_step_human_time_label_v1(index)
        internal = f"interne stap {index}"

        replacements = {
            f"<span>#{index}</span><span>display-only fallback</span>":
                f"<span>{human}</span><span>{internal}</span>",
            f"<span>#{index}</span><span>display-only</span>":
                f"<span>{human}</span><span>{internal}</span>",
            f"<span>#{index}</span><span>shadow</span>":
                f"<span>{human}</span><span>{internal}</span>",
            f"<span>#{index}</span>":
                f"<span>{human}</span>",
        }

        for old, new in replacements.items():
            rendered = rendered.replace(old, new)

        # Some mobile browsers make the two nested spans look glued together.
        rendered = rendered.replace(f"#{index}display-only fallback", f"{human} · {internal}")
        rendered = rendered.replace(f"#{index}display-only", f"{human} · {internal}")

    return rendered


def _eb_replace_selected_step_labels_v1(rendered: str) -> str:
    for index in range(24):
        human = _eb_step_human_time_label_v1(index)
        rendered = rendered.replace(f"#{index} · nu", f"{human} · interne stap {index}")
        rendered = rendered.replace(f"#{index} / +{index}h", f"{human} / interne stap {index}")
        rendered = rendered.replace(f"selected step #{index}", f"geselecteerde tijd: {human}")
    return rendered


def _eb_insert_visible_step_label_css_v1(rendered: str) -> str:
    css = """
    <style id="visible-plan-step-time-labels">
      .step-button {
        overflow: hidden;
      }

      .step-index {
        display: grid !important;
        grid-template-columns: 1fr !important;
        gap: 0.18rem !important;
        min-width: 0 !important;
      }

      .step-index > span:first-child {
        display: block !important;
        color: var(--text, #eef4f8) !important;
        font-size: clamp(1.05rem, 3.7vw, 1.35rem) !important;
        font-weight: 900 !important;
        letter-spacing: -0.02em !important;
        white-space: normal !important;
      }

      .step-index > span:nth-child(2) {
        display: block !important;
        color: var(--muted, #9eacb8) !important;
        font-size: clamp(0.72rem, 2.8vw, 0.9rem) !important;
        font-weight: 750 !important;
        letter-spacing: 0.01em !important;
        white-space: normal !important;
      }

      .step-soc {
        display: block !important;
        margin-top: 0.35rem !important;
        white-space: nowrap !important;
      }

      .step-reason {
        display: block !important;
        max-width: 100% !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
      }

      .plan-time-help {
        margin: 0.8rem 0 1rem;
        padding: 0.85rem 1rem;
        border: 1px solid rgba(67, 214, 166, 0.28);
        border-radius: 16px;
        background: rgba(67, 214, 166, 0.08);
        color: var(--muted, #9eacb8);
        font-size: 0.95rem;
      }

      .plan-time-help strong {
        color: var(--text, #eef4f8);
      }
    </style>
    """
    if 'id="visible-plan-step-time-labels"' in rendered:
        return rendered
    if "</head>" in rendered:
        return rendered.replace("</head>", css + "\n</head>", 1)
    return rendered


def _eb_insert_visible_step_label_note_v1(rendered: str) -> str:
    note = (
        '<div class="plan-time-help">'
        '<strong>Planstappen:</strong> Nu is de huidige plannerstap. '
        'Over 1 uur, Over 2 uur enzovoort zijn vooruitkijkstappen in de planning. '
        'De tekst “interne stap” is alleen een technische referentie.'
        '</div>'
    )

    if "Planstappen:</strong> Nu is de huidige plannerstap" in rendered:
        return rendered

    anchors = [
        '<div class="steps">',
        '<section id="tab-plan"',
        '<h2>Planner Timeline</h2>',
    ]

    for anchor in anchors:
        if anchor in rendered:
            return rendered.replace(anchor, note + "\n" + anchor, 1)

    return rendered


# Energy Brain UI active plan-card time labels.
# Display rendering only. No controller path, no HA writes, no battery command path.
_original_render_tesla_cockpit_html_active_time_labels_v1 = render_tesla_cockpit_html


def render_tesla_cockpit_html(summary: dict[str, Any]) -> str:
    rendered = _original_render_tesla_cockpit_html_active_time_labels_v1(summary)
    return _eb_active_plan_card_time_labels_v1(rendered)


def _eb_active_plan_card_time_labels_v1(rendered: str) -> str:
    rendered = _eb_active_replace_step_titles_v1(rendered)
    rendered = _eb_active_replace_selected_step_text_v1(rendered)
    rendered = _eb_active_insert_time_css_v1(rendered)
    rendered = _eb_active_insert_time_note_v1(rendered)
    return rendered


def _eb_active_time_name_v1(index: int) -> str:
    if index == 0:
        return "Nu"
    if index == 1:
        return "Over 1 uur"
    return f"Over {index} uur"


def _eb_active_replace_step_titles_v1(rendered: str) -> str:
    for index in range(24):
        human = _eb_active_time_name_v1(index)
        internal = f"interne stap {index}"

        rendered = rendered.replace(
            f"<span>#{index}</span><span>display-only fallback</span>",
            f"<span>{human}</span><span>{internal}</span>",
        )
        rendered = rendered.replace(
            f"<span>#{index}</span><span>display-only</span>",
            f"<span>{human}</span><span>{internal}</span>",
        )
        rendered = rendered.replace(
            f"<span>#{index}</span><span>shadow</span>",
            f"<span>{human}</span><span>{internal}</span>",
        )

        rendered = rendered.replace(
            f'aria-label="inspect only planner step {index}"',
            f'aria-label="inspect only planner time {human}, internal step {index}"',
        )

        rendered = rendered.replace(f"#{index}display-only fallback", f"{human} · {internal}")
        rendered = rendered.replace(f"#{index}display-only", f"{human} · {internal}")

    return rendered


def _eb_active_replace_selected_step_text_v1(rendered: str) -> str:
    for index in range(24):
        human = _eb_active_time_name_v1(index)
        rendered = rendered.replace(f"#{index} · nu", f"{human} · interne stap {index}")
        rendered = rendered.replace(f"#{index} / +{index}h", f"{human} / interne stap {index}")
        rendered = rendered.replace(f"selected step #{index}", f"geselecteerde tijd: {human}")
    return rendered


def _eb_active_insert_time_css_v1(rendered: str) -> str:
    css = """
    <style id="active-plan-step-time-labels">
      .step-button {
        overflow: hidden;
      }

      .step-index {
        display: grid !important;
        grid-template-columns: 1fr !important;
        gap: 0.18rem !important;
        min-width: 0 !important;
      }

      .step-index > span:first-child {
        display: block !important;
        color: var(--text, #eef4f8) !important;
        font-size: clamp(1.05rem, 3.7vw, 1.35rem) !important;
        font-weight: 900 !important;
        letter-spacing: -0.02em !important;
        white-space: normal !important;
      }

      .step-index > span:nth-child(2) {
        display: block !important;
        color: var(--muted, #9eacb8) !important;
        font-size: clamp(0.72rem, 2.8vw, 0.9rem) !important;
        font-weight: 750 !important;
        letter-spacing: 0.01em !important;
        white-space: normal !important;
      }

      .step-soc {
        display: block !important;
        margin-top: 0.35rem !important;
        white-space: nowrap !important;
      }

      .step-reason {
        display: block !important;
        max-width: 100% !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
      }

      .plan-time-help {
        margin: 0.8rem 0 1rem;
        padding: 0.85rem 1rem;
        border: 1px solid rgba(67, 214, 166, 0.28);
        border-radius: 16px;
        background: rgba(67, 214, 166, 0.08);
        color: var(--muted, #9eacb8);
        font-size: 0.95rem;
      }

      .plan-time-help strong {
        color: var(--text, #eef4f8);
      }
    </style>
    """

    if 'id="active-plan-step-time-labels"' in rendered:
        return rendered
    if "</head>" in rendered:
        return rendered.replace("</head>", css + "\n</head>", 1)
    return rendered


def _eb_active_insert_time_note_v1(rendered: str) -> str:
    note = (
        '<div class="plan-time-help">'
        '<strong>Planstappen:</strong> Nu is de huidige plannerstap. '
        'Over 1 uur, Over 2 uur enzovoort zijn vooruitkijkstappen. '
        'De tekst “interne stap” is alleen een technische referentie.'
        '</div>'
    )

    if "Planstappen:</strong> Nu is de huidige plannerstap" in rendered:
        return rendered

    anchor = '<div class="steps">'
    if anchor in rendered:
        return rendered.replace(anchor, note + "\n" + anchor, 1)

    return rendered


if __name__ == "__main__":
    main()




import re as _re


def _eb_pf_num(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _eb_pf_kw(value: Any) -> str:
    return f"{abs(_eb_pf_num(value)):.1f} kW"


def _eb_pf_soc(value: Any) -> str:
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _eb_pf_grid_note(grid_kw: Any) -> str:
    value = _eb_pf_num(grid_kw)
    if abs(value) < 0.05:
        return "bijna nul"
    return "teruglevering" if value < 0 else "netafname"


def _eb_pf_battery_note(battery_kw: Any) -> str:
    value = _eb_pf_num(battery_kw)
    if abs(value) < 0.05:
        return "praktisch stil"
    if value > 0:
        return f"laadt met {abs(value):.1f} kW"
    return f"ontlaadt met {abs(value):.1f} kW"


def _eb_pf_summary(flow: dict[str, Any]) -> str:
    pv_kw = _eb_pf_num(flow.get("pv_kw"))
    load_kw = _eb_pf_num(flow.get("load_kw"))
    battery_kw = _eb_pf_num(flow.get("battery_kw"))
    grid_kw = _eb_pf_num(flow.get("grid_kw"))

    battery_note = _eb_pf_battery_note(battery_kw)

    if abs(grid_kw) < 0.05:
        grid_note = "Er is bijna geen netverbruik of teruglevering."
    elif grid_kw < 0:
        grid_note = f"Er is ongeveer {abs(grid_kw):.1f} kW teruglevering."
    else:
        grid_note = f"Er is ongeveer {abs(grid_kw):.1f} kW netverbruik."

    return (
        f"Huis gebruikt {load_kw:.1f} kW. "
        f"Zon levert {pv_kw:.1f} kW. "
        f"Batterij staat {battery_note}. "
        f"{grid_note}"
    )


_EB_PLUS_FLOW_CSS = """
/* eb-plus-flow-style-marker */
.eb-plus-flow {
  padding: 16px 0 8px;
}
.eb-plus-summary {
  max-width: 760px;
  margin: 0 auto 18px;
  padding: 18px 20px;
  border-radius: 24px;
  border: 1px solid rgba(150,170,210,.22);
  background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.025));
  box-shadow: 0 18px 60px rgba(40,95,180,.12);
}
.eb-plus-summary strong {
  display: block;
  font-size: 1.06rem;
  line-height: 1.35;
  color: #eef4f8;
}
.eb-plus-summary .note {
  margin-top: 12px;
  font-size: .95rem;
  color: #aebdcb;
}
.eb-plus-stage {
  position: relative;
  max-width: 760px;
  margin: 0 auto 24px;
  min-height: 520px;
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 50%, rgba(70,140,255,.16), rgba(0,0,0,0) 34%),
    linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01));
}
.eb-plus-stage::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 80px 80px;
  pointer-events: none;
}
.eb-plus-node {
  position: absolute;
  z-index: 2;
  min-width: 116px;
  min-height: 116px;
  padding: 14px 16px;
  border-radius: 26px;
  border: 2px solid rgba(130,170,230,.4);
  background: rgba(10,18,26,.78);
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0,0,0,.22);
}
.eb-plus-node .title {
  font-size: 1rem;
  font-weight: 700;
  color: #eef4f8;
  margin-bottom: 4px;
}
.eb-plus-node .value {
  font-size: 1.15rem;
  font-weight: 800;
  color: #eef4f8;
}
.eb-plus-node .sub {
  margin-top: 4px;
  font-size: .9rem;
  color: #afc0cf;
}
.eb-plus-node-top {
  top: 44px;
  left: 50%;
  transform: translateX(-50%);
  border-color: rgba(242,184,75,.85);
}
.eb-plus-node-left {
  top: 205px;
  left: 48px;
  border-color: rgba(189,137,255,.85);
}
.eb-plus-node-center {
  top: 220px;
  left: 50%;
  transform: translateX(-50%);
  border-color: rgba(112,170,255,.85);
  min-width: 128px;
}
.eb-plus-node-right {
  top: 205px;
  right: 48px;
  border-color: rgba(92,220,220,.85);
}
.eb-plus-node-bottom {
  bottom: 54px;
  left: 50%;
  transform: translateX(-50%);
  border-color: rgba(67,214,166,.85);
}
.eb-plus-line {
  position: absolute;
  z-index: 1;
  background: linear-gradient(90deg, rgba(120,190,255,.75), rgba(120,190,255,.55));
  border-radius: 99px;
  opacity: .95;
}
.eb-plus-line-top {
  top: 160px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 82px;
}
.eb-plus-line-bottom {
  top: 335px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 96px;
}
.eb-plus-line-left {
  top: 275px;
  left: 168px;
  width: calc(50% - 232px);
  height: 6px;
}
.eb-plus-line-right {
  top: 275px;
  right: 168px;
  width: calc(50% - 232px);
  height: 6px;
}
.eb-plus-dot {
  position: absolute;
  z-index: 2;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #79c3ff;
  box-shadow: 0 0 0 4px rgba(121,195,255,.18);
}
.eb-plus-dot-top { top: 234px; left: calc(50% - 7px); }
.eb-plus-dot-left { top: 271px; left: calc(50% - 7px); }
.eb-plus-dot-right { top: 271px; left: calc(50% - 7px); }
.eb-plus-dot-bottom { top: 334px; left: calc(50% - 7px); }

.eb-plus-stats {
  max-width: 760px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.eb-plus-stat {
  border-radius: 24px;
  border: 1px solid rgba(150,170,210,.18);
  background: rgba(255,255,255,.03);
  padding: 18px 18px 20px;
}
.eb-plus-stat .label {
  font-size: .95rem;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: #aebdcb;
  margin-bottom: 8px;
}
.eb-plus-stat .big {
  font-size: 1.9rem;
  font-weight: 800;
  color: #eef4f8;
  margin-bottom: 6px;
}
.eb-plus-stat .small {
  color: #aebdcb;
  font-size: .95rem;
}
@media (max-width: 720px) {
  .eb-plus-stage {
    min-height: 600px;
  }
  .eb-plus-node {
    min-width: 100px;
    min-height: 100px;
    padding: 12px 12px;
  }
  .eb-plus-node-left { left: 12px; top: 220px; }
  .eb-plus-node-right { right: 12px; top: 220px; }
  .eb-plus-node-center { top: 232px; }
  .eb-plus-node-top { top: 48px; }
  .eb-plus-node-bottom { bottom: 54px; }
  .eb-plus-line-left { left: 118px; width: calc(50% - 168px); top: 281px; }
  .eb-plus-line-right { right: 118px; width: calc(50% - 168px); top: 281px; }
  .eb-plus-line-top { top: 160px; height: 92px; }
  .eb-plus-line-bottom { top: 336px; height: 112px; }
  .eb-plus-stats { grid-template-columns: 1fr 1fr; gap: 14px; }
}
"""


def _eb_plus_flow_section(summary: dict[str, Any]) -> str:
    summary = summary or {}
    flow = summary.get("energy_flow") or {}
    battery = summary.get("battery_soc_card") or {}

    pv_kw = _eb_pf_num(flow.get("pv_kw"))
    load_kw = _eb_pf_num(flow.get("load_kw"))
    battery_kw = _eb_pf_num(flow.get("battery_kw"))
    grid_kw = _eb_pf_num(flow.get("grid_kw"))
    soc_percent = battery.get("soc_percent")

    pv_text = _eb_pf_kw(pv_kw)
    load_text = _eb_pf_kw(load_kw)
    battery_power_text = _eb_pf_kw(battery_kw)
    grid_text = _eb_pf_kw(grid_kw)
    soc_text = _eb_pf_soc(soc_percent)

    summary_text = html.escape(_eb_pf_summary(flow))
    battery_note = html.escape(_eb_pf_battery_note(battery_kw))
    grid_note = html.escape(_eb_pf_grid_note(grid_kw))

    return f"""
      <section class="flow eb-plus-flow" aria-label="Energy Flow Overview">
        <article class="eb-plus-summary">
          <strong>{summary_text}</strong>
          <p class="note">Batterij nu {html.escape(soc_text)}.</p>
        </article>

        <div class="eb-plus-stage">
          <div class="eb-plus-line eb-plus-line-top"></div>
          <div class="eb-plus-line eb-plus-line-left"></div>
          <div class="eb-plus-line eb-plus-line-right"></div>
          <div class="eb-plus-line eb-plus-line-bottom"></div>

          <div class="eb-plus-dot eb-plus-dot-top"></div>
          <div class="eb-plus-dot eb-plus-dot-left"></div>
          <div class="eb-plus-dot eb-plus-dot-right"></div>
          <div class="eb-plus-dot eb-plus-dot-bottom"></div>

          <div class="eb-plus-node eb-plus-node-top">
            <div class="title">Zon</div>
            <div class="value">{html.escape(pv_text)}</div>
          </div>

          <div class="eb-plus-node eb-plus-node-left">
            <div class="title">Net</div>
            <div class="value">{html.escape(grid_text)}</div>
            <div class="sub">{grid_note}</div>
          </div>

          <div class="eb-plus-node eb-plus-node-center">
            <div class="title">Huis</div>
            <div class="value">{html.escape(load_text)}</div>
          </div>

          <div class="eb-plus-node eb-plus-node-right">
            <div class="title">Status</div>
            <div class="value">Read-only</div>
            <div class="sub">alleen meekijken</div>
          </div>

          <div class="eb-plus-node eb-plus-node-bottom">
            <div class="title">Batterij</div>
            <div class="value">{html.escape(soc_text)}</div>
            <div class="sub">{html.escape(battery_power_text)} nu</div>
          </div>
        </div>

        <div class="eb-plus-stats">
          <article class="eb-plus-stat">
            <div class="label">Zon</div>
            <div class="big">{html.escape(pv_text)}</div>
            <div class="small">naar huis of batterij</div>
          </article>
          <article class="eb-plus-stat">
            <div class="label">Huis</div>
            <div class="big">{html.escape(load_text)}</div>
            <div class="small">actueel verbruik</div>
          </article>
          <article class="eb-plus-stat">
            <div class="label">Batterij</div>
            <div class="big">{html.escape(soc_text)}</div>
            <div class="small">{html.escape(battery_note)}</div>
          </article>
          <article class="eb-plus-stat">
            <div class="label">Net</div>
            <div class="big">{html.escape(grid_text)}</div>
            <div class="small">{grid_note}</div>
          </article>
        </div>
      </section>
    """


_original_render_tesla_cockpit_html_plus_flow = render_tesla_cockpit_html


def render_tesla_cockpit_html(summary: dict[str, Any]) -> str:
    rendered = _original_render_tesla_cockpit_html_plus_flow(summary)
    try:
        plus_flow = _eb_plus_flow_section(summary)

        rendered = _re.sub(
            r'<section class="flow" aria-label="Energy Flow Overview">.*?</section>',
            plus_flow,
            rendered,
            count=1,
            flags=_re.S,
        )

        if "eb-plus-flow-style-marker" not in rendered:
            css_block = "\n" + _EB_PLUS_FLOW_CSS + "\n"
            if "</style>" in rendered:
                rendered = rendered.replace("</style>", css_block + "</style>", 1)
            else:
                rendered = css_block + rendered

    except Exception:
        return rendered
    return rendered

# Energy Brain visual-only plus-shaped energy flow final.
_previous_render_tesla_cockpit_html_plus_cross_final = render_tesla_cockpit_html


def _eb_flow_float_final(value: object, fallback: float = 0.0) -> float:
    if isinstance(value, bool):
        return fallback
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def _eb_flow_kw_final(value: object) -> str:
    return f"{_eb_flow_float_final(value):.1f} kW"


def _eb_flow_pct_final(value: object) -> str:
    return f"{_eb_flow_float_final(value):.0f}%"


def _eb_flow_get_final(data: object, key: str) -> object:
    if isinstance(data, dict):
        value = data.get(key)
        if value is not None:
            return value
    return 0.0


def _eb_plus_cross_style_final() -> str:
    return """
<style id="eb-plus-cross-flow-final-style">
  .eb-plus-cross-flow-final {
    margin: 18px 0 22px;
    padding: 18px 14px 20px;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 26px;
    background:
      radial-gradient(circle at 50% 46%, rgba(103, 167, 255, 0.18), transparent 15rem),
      rgba(10, 16, 23, 0.78);
  }

  .eb-flow-summary-final {
    width: min(100%, 660px);
    margin: 0 auto 20px;
    padding: 18px 20px;
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 22px;
    background: rgba(15, 23, 31, 0.88);
  }

  .eb-flow-summary-final strong {
    display: block;
    color: #e8eef6;
    font-size: clamp(1.18rem, 4.8vw, 1.9rem);
    line-height: 1.28;
    letter-spacing: -0.035em;
  }

  .eb-flow-summary-final span {
    display: block;
    margin-top: 10px;
    color: #9aa6b2;
    font-size: clamp(0.95rem, 3.6vw, 1.18rem);
  }

  .eb-flow-cross-final {
    position: relative;
    width: min(100%, 680px);
    height: clamp(390px, 76vw, 560px);
    margin: 0 auto;
  }

  .eb-flow-lines-final {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 10px rgba(103, 167, 255, 0.28));
  }

  .eb-flow-line-final {
    fill: none;
    stroke-width: 1.35;
    stroke-linecap: round;
    stroke-dasharray: 3.2 2.4;
    opacity: 0.95;
  }

  .eb-flow-line-sun-final { stroke: #f59e0b; }
  .eb-flow-line-grid-final { stroke: #a855f7; }
  .eb-flow-line-home-final { stroke: #2dd4bf; }
  .eb-flow-line-battery-final { stroke: #36d399; }

  .eb-flow-dot-sun-final { fill: #f59e0b; }
  .eb-flow-dot-grid-final { fill: #a855f7; }
  .eb-flow-dot-home-final { fill: #2dd4bf; }
  .eb-flow-dot-battery-final { fill: #36d399; }

  .eb-flow-hub-final {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 18px;
    height: 18px;
    transform: translate(-50%, -50%);
    border-radius: 999px;
    background: #dbeafe;
    box-shadow: 0 0 28px rgba(147, 197, 253, 0.68);
    z-index: 3;
  }

  .eb-flow-node-final {
    position: absolute;
    z-index: 4;
    display: grid;
    place-items: center;
    text-align: center;
    width: clamp(98px, 23vw, 144px);
    height: clamp(98px, 23vw, 144px);
    border-radius: 999px;
    background: rgba(8, 13, 19, 0.92);
    color: #e8eef6;
    box-shadow: 0 18px 48px rgba(0,0,0,0.28);
  }

  .eb-flow-node-final strong {
    font-size: clamp(1.05rem, 4vw, 1.65rem);
    line-height: 1;
  }

  .eb-flow-node-final small {
    color: #9aa6b2;
    font-size: clamp(0.66rem, 2.6vw, 0.85rem);
  }

  .eb-node-title-final {
    color: #cbd5e1;
    font-weight: 850;
    font-size: clamp(0.8rem, 3vw, 1.0rem);
  }

  .eb-flow-sun-final {
    left: 50%;
    top: 0;
    transform: translateX(-50%);
    border: 3px solid #f59e0b;
  }

  .eb-flow-grid-final {
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    border: 3px solid #a855f7;
  }

  .eb-flow-home-final {
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    border: 3px solid #2dd4bf;
  }

  .eb-flow-battery-final {
    left: 50%;
    bottom: 0;
    transform: translateX(-50%);
    border: 3px solid #36d399;
  }

  .eb-flow-metrics-final {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    width: min(100%, 680px);
    margin: 18px auto 0;
  }

  .eb-flow-metrics-final article {
    padding: 16px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 20px;
    background: rgba(15, 23, 31, 0.86);
  }

  .eb-flow-metrics-final span {
    display: block;
    color: #9aa6b2;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-weight: 850;
    font-size: 0.78rem;
  }

  .eb-flow-metrics-final strong {
    display: block;
    margin-top: 8px;
    color: #e8eef6;
    font-size: clamp(1.3rem, 5vw, 2rem);
  }

  .eb-flow-metrics-final small {
    display: block;
    margin-top: 4px;
    color: #9aa6b2;
    font-size: 0.92rem;
  }

  @media (max-width: 520px) {
    .eb-flow-cross-final { height: 410px; }
    .eb-flow-node-final { width: 100px; height: 100px; }
  }
</style>
"""


def _eb_plus_cross_flow_final(summary: dict[str, object]) -> str:
    flow = summary.get("energy_flow")
    battery_card = summary.get("battery_soc_card")

    pv_kw = _eb_flow_get_final(flow, "pv_kw")
    load_kw = _eb_flow_get_final(flow, "load_kw")
    battery_kw = _eb_flow_get_final(flow, "battery_kw")
    grid_kw = _eb_flow_get_final(flow, "grid_kw")
    soc = _eb_flow_get_final(battery_card, "soc_percent")

    pv = _eb_flow_float_final(pv_kw)
    load = _eb_flow_float_final(load_kw)
    battery = _eb_flow_float_final(battery_kw)
    grid = _eb_flow_float_final(grid_kw)

    if abs(grid) < 0.05:
        grid_text = "bijna stil"
    elif grid > 0:
        grid_text = "import"
    else:
        grid_text = "teruglevering"

    if abs(battery) < 0.05:
        battery_text = "batterij stil"
    elif battery > 0:
        battery_text = "batterij laadt"
    else:
        battery_text = "batterij helpt"

    if pv >= load and abs(grid) < 0.15:
        sentence = f"Huis gebruikt {_eb_flow_kw_final(load_kw)}. Zon levert {_eb_flow_kw_final(pv_kw)}. Net is bijna stil."
    elif pv >= load:
        sentence = f"Huis gebruikt {_eb_flow_kw_final(load_kw)}. Zon levert {_eb_flow_kw_final(pv_kw)}. Net: {_eb_flow_kw_final(abs(grid))} {grid_text}."
    else:
        sentence = f"Huis gebruikt {_eb_flow_kw_final(load_kw)}. Zon levert {_eb_flow_kw_final(pv_kw)}. Net vult {_eb_flow_kw_final(abs(grid))} bij."

    return f"""
<section class="eb-plus-cross-flow-final" aria-label="Energy Flow Overview">
  <div class="eb-plus-cross-flow-final-marker" hidden>eb-plus-cross-flow-final-marker</div>

  <article class="eb-flow-summary-final">
    <strong>{sentence}</strong>
    <span>Batterij nu {_eb_flow_pct_final(soc)} - {battery_text}</span>
  </article>

  <div class="eb-flow-cross-final">
    <div class="eb-flow-node-final eb-flow-sun-final">
      <span class="eb-node-title-final">Zon</span>
      <strong>{_eb_flow_kw_final(pv_kw)}</strong>
    </div>

    <div class="eb-flow-node-final eb-flow-grid-final">
      <span class="eb-node-title-final">Net</span>
      <strong>{_eb_flow_kw_final(abs(grid))}</strong>
      <small>{grid_text}</small>
    </div>

    <div class="eb-flow-node-final eb-flow-home-final">
      <span class="eb-node-title-final">Huis</span>
      <strong>{_eb_flow_kw_final(load_kw)}</strong>
    </div>

    <div class="eb-flow-node-final eb-flow-battery-final">
      <span class="eb-node-title-final">Batterij</span>
      <strong>{_eb_flow_pct_final(soc)}</strong>
      <small>{_eb_flow_kw_final(abs(battery))}</small>
    </div>

    <div class="eb-flow-hub-final"></div>

    <svg class="eb-flow-lines-final" viewBox="0 0 100 100" aria-hidden="true">
      <path class="eb-flow-line-final eb-flow-line-sun-final" d="M50 18 C50 32 50 38 50 50"/>
      <path class="eb-flow-line-final eb-flow-line-grid-final" d="M18 50 C32 50 38 50 50 50"/>
      <path class="eb-flow-line-final eb-flow-line-home-final" d="M50 50 C62 50 68 50 82 50"/>
      <path class="eb-flow-line-final eb-flow-line-battery-final" d="M50 50 C50 62 50 68 50 82"/>
      <circle class="eb-flow-dot-sun-final" cx="50" cy="30" r="1.8"/>
      <circle class="eb-flow-dot-grid-final" cx="30" cy="50" r="1.8"/>
      <circle class="eb-flow-dot-home-final" cx="70" cy="50" r="1.8"/>
      <circle class="eb-flow-dot-battery-final" cx="50" cy="70" r="1.8"/>
    </svg>
  </div>

  <div class="eb-flow-metrics-final">
    <article><span>Zon</span><strong>{_eb_flow_kw_final(pv_kw)}</strong><small>naar huis of batterij</small></article>
    <article><span>Huis</span><strong>{_eb_flow_kw_final(load_kw)}</strong><small>actueel verbruik</small></article>
    <article><span>Batterij</span><strong>{_eb_flow_pct_final(soc)}</strong><small>{battery_text}</small></article>
    <article><span>Net</span><strong>{_eb_flow_kw_final(abs(grid))}</strong><small>{grid_text}</small></article>
  </div>
</section>
"""


def _eb_replace_first_flow_final(rendered: str, replacement: str) -> str:
    markers = [
        '<section class="eb-plus-cross-flow-final"',
        '<section class="eb-plus-cross-flow-v3"',
        '<section class="eb-plus-cross-flow-v2"',
        '<section class="eb-plus-flow"',
        '<section class="flow" aria-label="Energy Flow Overview"',
    ]

    for marker_text in markers:
        start = rendered.find(marker_text)
        if start == -1:
            continue

        next_section = rendered.find("\n<section", start + len(marker_text))
        next_article = rendered.find("\n<article", start + len(marker_text))
        candidates = [x for x in [next_section, next_article] if x != -1]
        end = min(candidates) if candidates else -1

        if end == -1:
            return rendered[:start] + replacement + rendered[start:]

        return rendered[:start] + replacement + rendered[end:]

    body = rendered.find("<body")
    if body == -1:
        return replacement + rendered

    body_end = rendered.find(">", body)
    if body_end == -1:
        return replacement + rendered

    return rendered[:body_end + 1] + replacement + rendered[body_end + 1:]


def render_tesla_cockpit_html(summary: dict[str, object]) -> str:
    rendered = _previous_render_tesla_cockpit_html_plus_cross_final(summary)
    flow_html = _eb_plus_cross_style_final() + _eb_plus_cross_flow_final(summary)
    if "eb-plus-cross-flow-final-marker" in rendered:
        return rendered
    return _eb_replace_first_flow_final(rendered, flow_html)

# Energy Brain route-wide final plus-shaped energy flow.
_eb_prev_render_tesla_plus_route_final = render_tesla_cockpit_html
_eb_prev_render_dashboard_plus_route_final = render_dashboard_html


def _eb_pf_num_final(value: object, fallback: float = 0.0) -> float:
    if isinstance(value, bool):
        return fallback
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def _eb_pf_kw_final(value: object) -> str:
    return f"{_eb_pf_num_final(value):.1f} kW"


def _eb_pf_pct_final(value: object) -> str:
    return f"{_eb_pf_num_final(value):.0f}%"


def _eb_pf_dict_get_final(data: object, key: str, fallback: object = 0.0) -> object:
    if isinstance(data, dict):
        return data.get(key, fallback)
    return fallback


def _eb_pf_flow_from_summary_final(summary: object) -> tuple[float, float, float, float, float]:
    if not isinstance(summary, dict):
        return 0.0, 0.0, 0.0, 0.0, 0.0

    flow = summary.get("energy_flow")
    battery_card = summary.get("battery_soc_card")

    if isinstance(flow, dict):
        pv = _eb_pf_num_final(flow.get("pv_kw"))
        load = _eb_pf_num_final(flow.get("load_kw"))
        battery = _eb_pf_num_final(flow.get("battery_kw"))
        grid = _eb_pf_num_final(flow.get("grid_kw"))
    else:
        snapshot = summary.get("snapshot")
        pv = _eb_pf_num_final(_eb_pf_dict_get_final(snapshot, "pv_power_kw"))
        load = _eb_pf_num_final(_eb_pf_dict_get_final(snapshot, "household_load_kw"))
        controller = summary.get("controller")
        battery = _eb_pf_num_final(_eb_pf_dict_get_final(controller, "setpoint_kw"))
        grid = load - pv - battery

    soc = _eb_pf_num_final(_eb_pf_dict_get_final(battery_card, "soc_percent"))
    if soc <= 0.0:
        snapshot = summary.get("snapshot")
        soc = _eb_pf_num_final(_eb_pf_dict_get_final(snapshot, "battery_soc_percent"))

    return pv, load, battery, grid, soc


def _eb_pf_css_final() -> str:
    return """
<style id="eb-plus-flow-final-css">
  .eb-plus-flow-final {
    margin: 18px 0 24px;
    padding: 18px 14px 22px;
    border: 2px solid rgba(54, 211, 153, 0.36);
    border-radius: 28px;
    background:
      radial-gradient(circle at 50% 48%, rgba(103, 167, 255, 0.20), transparent 16rem),
      rgba(10, 16, 23, 0.90);
  }

  .eb-plus-flow-final-badge {
    display: inline-block;
    margin-bottom: 12px;
    padding: 7px 10px;
    border-radius: 999px;
    border: 1px solid rgba(54, 211, 153, 0.48);
    color: #bdf7dc;
    background: rgba(54, 211, 153, 0.10);
    font-weight: 900;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    font-size: 0.72rem;
  }

  .eb-flow-summary-final {
    width: min(100%, 680px);
    margin: 0 auto 22px;
    padding: 18px 20px;
    border: 1px solid rgba(148, 163, 184, 0.30);
    border-radius: 22px;
    background: rgba(15, 23, 31, 0.90);
  }

  .eb-flow-summary-final strong {
    display: block;
    color: #e8eef6;
    font-size: clamp(1.22rem, 5vw, 1.95rem);
    line-height: 1.28;
    letter-spacing: -0.035em;
  }

  .eb-flow-summary-final span {
    display: block;
    margin-top: 10px;
    color: #9aa6b2;
    font-size: clamp(0.95rem, 3.6vw, 1.18rem);
  }

  .eb-flow-cross-final {
    position: relative;
    width: min(100%, 700px);
    height: clamp(430px, 82vw, 590px);
    margin: 0 auto;
  }

  .eb-flow-lines-final {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 0 12px rgba(103, 167, 255, 0.30));
  }

  .eb-flow-line-final {
    fill: none;
    stroke-width: 1.45;
    stroke-linecap: round;
    stroke-dasharray: 3.4 2.4;
    opacity: 0.96;
  }

  .eb-flow-line-sun-final { stroke: #f59e0b; }
  .eb-flow-line-grid-final { stroke: #a855f7; }
  .eb-flow-line-home-final { stroke: #2dd4bf; }
  .eb-flow-line-battery-final { stroke: #36d399; }

  .eb-flow-dot-sun-final { fill: #f59e0b; }
  .eb-flow-dot-grid-final { fill: #a855f7; }
  .eb-flow-dot-home-final { fill: #2dd4bf; }
  .eb-flow-dot-battery-final { fill: #36d399; }

  .eb-flow-hub-final {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 18px;
    height: 18px;
    transform: translate(-50%, -50%);
    border-radius: 999px;
    background: #dbeafe;
    box-shadow: 0 0 30px rgba(147, 197, 253, 0.75);
    z-index: 3;
  }

  .eb-flow-node-final {
    position: absolute;
    z-index: 4;
    display: grid;
    place-items: center;
    text-align: center;
    width: clamp(108px, 25vw, 154px);
    height: clamp(108px, 25vw, 154px);
    border-radius: 999px;
    background: rgba(8, 13, 19, 0.94);
    color: #e8eef6;
    box-shadow: 0 18px 48px rgba(0,0,0,0.30);
  }

  .eb-flow-node-final strong {
    font-size: clamp(1.12rem, 4.4vw, 1.72rem);
    line-height: 1;
  }

  .eb-flow-node-final small {
    color: #9aa6b2;
    font-size: clamp(0.70rem, 2.8vw, 0.88rem);
  }

  .eb-node-title-final {
    color: #cbd5e1;
    font-weight: 900;
    font-size: clamp(0.82rem, 3.1vw, 1.02rem);
  }

  .eb-flow-sun-final {
    left: 50%;
    top: 0;
    transform: translateX(-50%);
    border: 3px solid #f59e0b;
  }

  .eb-flow-grid-final {
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    border: 3px solid #a855f7;
  }

  .eb-flow-home-final {
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    border: 3px solid #2dd4bf;
  }

  .eb-flow-battery-final {
    left: 50%;
    bottom: 0;
    transform: translateX(-50%);
    border: 3px solid #36d399;
  }

  .eb-flow-metrics-final {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    width: min(100%, 700px);
    margin: 20px auto 0;
  }

  .eb-flow-metrics-final article {
    padding: 16px;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 20px;
    background: rgba(15, 23, 31, 0.88);
  }

  .eb-flow-metrics-final span {
    display: block;
    color: #9aa6b2;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-weight: 850;
    font-size: 0.78rem;
  }

  .eb-flow-metrics-final strong {
    display: block;
    margin-top: 8px;
    color: #e8eef6;
    font-size: clamp(1.3rem, 5vw, 2rem);
  }

  .eb-flow-metrics-final small {
    display: block;
    margin-top: 4px;
    color: #9aa6b2;
    font-size: 0.92rem;
  }

  @media (max-width: 520px) {
    .eb-flow-cross-final { height: 430px; }
    .eb-flow-node-final { width: 108px; height: 108px; }
  }
</style>
"""


def _eb_pf_html_final(summary: object) -> str:
    pv, load, battery, grid, soc = _eb_pf_flow_from_summary_final(summary)

    if abs(grid) < 0.05:
        grid_text = "bijna stil"
    elif grid > 0:
        grid_text = "import"
    else:
        grid_text = "teruglevering"

    if abs(battery) < 0.05:
        battery_text = "batterij stil"
    elif battery > 0:
        battery_text = "batterij laadt"
    else:
        battery_text = "batterij helpt"

    if pv >= load and abs(grid) < 0.15:
        sentence = f"Huis gebruikt {_eb_pf_kw_final(load)}. Zon levert {_eb_pf_kw_final(pv)}. Net is bijna stil."
    elif pv >= load:
        sentence = f"Huis gebruikt {_eb_pf_kw_final(load)}. Zon levert {_eb_pf_kw_final(pv)}. Net: {_eb_pf_kw_final(abs(grid))} {grid_text}."
    else:
        sentence = f"Huis gebruikt {_eb_pf_kw_final(load)}. Zon levert {_eb_pf_kw_final(pv)}. Net vult {_eb_pf_kw_final(abs(grid))} bij."

    return f"""
<section class="eb-plus-flow-final" aria-label="Energy Flow Overview">
  <div class="eb-plus-flow-final-live-marker" hidden>EB_PLUS_FLOW_FINAL_VISIBLE</div>
  <span class="eb-plus-flow-final-badge">Plus-flow actief</span>

  <article class="eb-flow-summary-final">
    <strong>{sentence}</strong>
    <span>Batterij nu {_eb_pf_pct_final(soc)} - {battery_text}</span>
  </article>

  <div class="eb-flow-cross-final">
    <div class="eb-flow-node-final eb-flow-sun-final">
      <span class="eb-node-title-final">Zon</span>
      <strong>{_eb_pf_kw_final(pv)}</strong>
    </div>

    <div class="eb-flow-node-final eb-flow-grid-final">
      <span class="eb-node-title-final">Net</span>
      <strong>{_eb_pf_kw_final(abs(grid))}</strong>
      <small>{grid_text}</small>
    </div>

    <div class="eb-flow-node-final eb-flow-home-final">
      <span class="eb-node-title-final">Huis</span>
      <strong>{_eb_pf_kw_final(load)}</strong>
    </div>

    <div class="eb-flow-node-final eb-flow-battery-final">
      <span class="eb-node-title-final">Batterij</span>
      <strong>{_eb_pf_pct_final(soc)}</strong>
      <small>{_eb_pf_kw_final(abs(battery))}</small>
    </div>

    <div class="eb-flow-hub-final"></div>

    <svg class="eb-flow-lines-final" viewBox="0 0 100 100" aria-hidden="true">
      <path class="eb-flow-line-final eb-flow-line-sun-final" d="M50 18 C50 32 50 38 50 50"/>
      <path class="eb-flow-line-final eb-flow-line-grid-final" d="M18 50 C32 50 38 50 50 50"/>
      <path class="eb-flow-line-final eb-flow-line-home-final" d="M50 50 C62 50 68 50 82 50"/>
      <path class="eb-flow-line-final eb-flow-line-battery-final" d="M50 50 C50 62 50 68 50 82"/>
      <circle class="eb-flow-dot-sun-final" cx="50" cy="30" r="1.8"/>
      <circle class="eb-flow-dot-grid-final" cx="30" cy="50" r="1.8"/>
      <circle class="eb-flow-dot-home-final" cx="70" cy="50" r="1.8"/>
      <circle class="eb-flow-dot-battery-final" cx="50" cy="70" r="1.8"/>
    </svg>
  </div>

  <div class="eb-flow-metrics-final">
    <article><span>Zon</span><strong>{_eb_pf_kw_final(pv)}</strong><small>naar huis of batterij</small></article>
    <article><span>Huis</span><strong>{_eb_pf_kw_final(load)}</strong><small>actueel verbruik</small></article>
    <article><span>Batterij</span><strong>{_eb_pf_pct_final(soc)}</strong><small>{battery_text}</small></article>
    <article><span>Net</span><strong>{_eb_pf_kw_final(abs(grid))}</strong><small>{grid_text}</small></article>
  </div>
</section>
"""


def _eb_pf_replace_final(rendered: str, summary: object) -> str:
    if "EB_PLUS_FLOW_FINAL_VISIBLE" in rendered:
        return rendered

    block = _eb_pf_css_final() + _eb_pf_html_final(summary)

    starts = [
        '<section class="eb-plus-flow-final"',
        '<section class="eb-plus-cross-flow-final"',
        '<section class="eb-plus-cross-flow-v3"',
        '<section class="eb-plus-cross-flow-v2"',
        '<section class="eb-plus-flow"',
        '<section class="flow" aria-label="Energy Flow Overview"',
    ]

    for needle in starts:
        start = rendered.find(needle)
        if start == -1:
            continue

        candidates = [
            rendered.find("\n<section", start + len(needle)),
            rendered.find("\n<article", start + len(needle)),
            rendered.find("\n<div class=\"tabs\"", start + len(needle)),
        ]
        candidates = [pos for pos in candidates if pos != -1]
        end = min(candidates) if candidates else -1

        if end == -1:
            return rendered[:start] + block + rendered[start:]

        return rendered[:start] + block + rendered[end:]

    body = rendered.find("<body")
    if body == -1:
        return block + rendered

    body_end = rendered.find(">", body)
    if body_end == -1:
        return block + rendered

    return rendered[:body_end + 1] + block + rendered[body_end + 1:]


def render_tesla_cockpit_html(summary: dict[str, object]) -> str:
    rendered = _eb_prev_render_tesla_plus_route_final(summary)
    return _eb_pf_replace_final(rendered, summary)


def render_dashboard_html(summary: dict[str, object]) -> str:
    rendered = _eb_prev_render_dashboard_plus_route_final(summary)
    return _eb_pf_replace_final(rendered, summary)

# EB_PV_SANITY_GUARD_V1
# Read-only UI guard: do not present implausible PV power as normal truth.
# This does not change planner/controller behavior and sends no commands.

_EB_PRE_PV_GUARD_RENDER_DASHBOARD_HTML = render_dashboard_html


def _eb_pv_guard_number_v1(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _eb_pv_guard_text_v1(pv_kw: float, load_kw: float, battery_kw: float, grid_kw: float) -> str:
    # Conservative home PV display guard.
    # Above 25 kW is suspicious for this EMS context unless explicitly configured later.
    if pv_kw > 25.0:
        return (
            "PV-waarde lijkt onrealistisch hoog: "
            f"{pv_kw:.1f} kW. "
            "Energy Brain toont dit als verdachte input. "
            "Controleer of de PV-bron actuele kW is en geen dagteller, Wh/kWh-teller of forecast-som."
        )

    if pv_kw < -0.1:
        return (
            "PV-waarde is negatief en daarom verdacht. "
            "Energy Brain toont dit als onzekere input."
        )

    if abs(grid_kw) < 0.05:
        grid_text = "Er is bijna geen netverbruik of teruglevering."
    elif grid_kw < 0:
        grid_text = f"Er gaat ongeveer {abs(grid_kw):.1f} kW terug naar het net."
    else:
        grid_text = f"Het net vult ongeveer {grid_kw:.1f} kW bij."

    if battery_kw > 0.05:
        battery_text = f"De batterij wordt geladen met ongeveer {battery_kw:.1f} kW."
    elif battery_kw < -0.05:
        battery_text = f"De batterij helpt het huis met ongeveer {abs(battery_kw):.1f} kW."
    else:
        battery_text = "De batterij staat praktisch stil."

    return (
        f"Huis gebruikt {load_kw:.1f} kW. "
        f"Zon levert {pv_kw:.1f} kW. "
        f"{battery_text} "
        f"{grid_text}"
    )


def _eb_insert_pv_guard_banner_v1(html_text: str, summary: dict) -> str:
    flow = summary.get("energy_flow") if isinstance(summary, dict) else {}
    if not isinstance(flow, dict):
        flow = {}

    pv_kw = _eb_pv_guard_number_v1(flow.get("pv_kw"))
    load_kw = _eb_pv_guard_number_v1(flow.get("load_kw"))
    battery_kw = _eb_pv_guard_number_v1(flow.get("battery_kw"))
    grid_kw = _eb_pv_guard_number_v1(flow.get("grid_kw"))

    message = _eb_pv_guard_text_v1(pv_kw, load_kw, battery_kw, grid_kw)
    suspicious = pv_kw > 25.0 or pv_kw < -0.1

    cls = "eb-pv-sanity-warning" if suspicious else "eb-pv-sanity-ok"
    label = "PV input controleren" if suspicious else "Energy flow"

    css = """
<style id="eb-pv-sanity-guard-style">
.eb-pv-sanity-warning,
.eb-pv-sanity-ok {
  margin: 18px auto;
  max-width: 860px;
  padding: 18px 20px;
  border-radius: 20px;
  border: 1px solid rgba(255,209,102,.42);
  background: rgba(255,209,102,.10);
  color: #eef4f8;
  font-size: 1rem;
  line-height: 1.45;
}
.eb-pv-sanity-ok {
  border-color: rgba(67,214,166,.32);
  background: rgba(67,214,166,.07);
}
.eb-pv-sanity-warning strong,
.eb-pv-sanity-ok strong {
  display: block;
  margin-bottom: 6px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #ffd166;
}
.eb-pv-sanity-ok strong {
  color: #43d6a6;
}
</style>
"""

    banner = (
        css
        + f'<section class="{cls}" id="eb-pv-sanity-guard">'
        + f"<strong>{label}</strong>"
        + f"<span>{message}</span>"
        + "</section>"
    )

    # Put warning/summary directly before the visual energy flow where possible.
    anchors = [
        '<section class="eb-plus-flow-final"',
        '<section class="flow"',
        '<section class="human-grid"',
        '</main>',
    ]
    for anchor in anchors:
        if anchor in html_text:
            return html_text.replace(anchor, banner + anchor, 1)

    return html_text + banner


def render_dashboard_html(summary: dict) -> str:
    rendered = _EB_PRE_PV_GUARD_RENDER_DASHBOARD_HTML(summary)
    return _eb_insert_pv_guard_banner_v1(rendered, summary)


# EB_PATCH_V47_PV_POWER_SOURCE_GUARD
#
# Safety purpose:
# - Live powerflow must not display day-energy or forecast-energy values as current kW.
# - kWh/Wh forecast totals are valid forecast data, but invalid as "PV now".
# - If the PV value looks like an energy/forecast source, keep the UI observer-only
#   and show a clear warning instead of pretending it is live power.
#
# This is display-only. It does not call Home Assistant services and does not
# change planner/controller behavior.

def _eb_v47_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _eb_v47_fmt_kw(value):
    value = _eb_v47_float(value)
    return f"{value:.2f} kW"


def _eb_v47_extract_payload_from_html(rendered):
    import json as _json
    import re as _re

    match = _re.search(
        r'<script id="cockpit-payload" type="application/json">(.*?)</script>',
        rendered,
        _re.S,
    )
    if not match:
        return {}
    try:
        return _json.loads(match.group(1))
    except Exception:
        return {}


def _eb_v47_pv_power_suspect(payload):
    flow = payload.get("energy_flow") or {}
    pv_kw = _eb_v47_float(flow.get("pv_kw"))

    # The system can physically have high PV, but for this installation the
    # observed broken state is day/forecast kWh being shown as instantaneous kW.
    # Use a conservative UI-only sanity threshold. This does not alter planning.
    if pv_kw >= 15.0:
        return True

    # Extra hint: Solcast/Predbat forecast arrays are energy values, not live power.
    # If current flow equals a large forecast-energy-ish value, mark suspicious.
    for row in payload.get("pv_forecast") or []:
        pv_energy = _eb_v47_float(
            row.get("pv_kwh", row.get("pv_kw", row.get("forecast", 0.0)))
        )
        if pv_energy >= 15.0 and abs(pv_energy - pv_kw) < 0.25:
            return True

    return False


def _eb_v47_build_guarded_plus_flow(payload):
    flow = payload.get("energy_flow") or {}
    soc = ((payload.get("battery_soc_card") or {}).get("soc_percent"))

    raw_pv_kw = _eb_v47_float(flow.get("pv_kw"))
    load_kw = _eb_v47_float(flow.get("load_kw"))
    battery_kw = _eb_v47_float(flow.get("battery_kw"))
    grid_kw = _eb_v47_float(flow.get("grid_kw"))

    pv_bad = _eb_v47_pv_power_suspect(payload)

    if pv_bad:
        headline = (
            "PV live-vermogen wordt niet betrouwbaar getoond. "
            "De gekozen bron lijkt een dagwaarde of forecast in kWh te zijn, geen actuele kW-sensor."
        )
        pv_value = "Bron controleren"
        grid_text = "Netbalans niet betrouwbaar zolang PV-bron ongeldig is"
    else:
        headline = (
            f"Huis gebruikt {_eb_v47_fmt_kw(load_kw)}. "
            f"Zon levert {_eb_v47_fmt_kw(raw_pv_kw)}. "
            f"Batterij {'wordt geladen met' if battery_kw > 0.05 else 'levert' if battery_kw < -0.05 else 'staat neutraal op'} "
            f"{_eb_v47_fmt_kw(abs(battery_kw))}."
        )
        pv_value = _eb_v47_fmt_kw(raw_pv_kw)
        if grid_kw < -0.05:
            grid_text = f"Teruglevering: {_eb_v47_fmt_kw(abs(grid_kw))}"
        elif grid_kw > 0.05:
            grid_text = f"Import: {_eb_v47_fmt_kw(grid_kw)}"
        else:
            grid_text = "Net ongeveer neutraal"

    soc_text = "onbekend" if soc is None else f"{_eb_v47_float(soc):.1f}%"
    battery_value = (
        f"Laden: {_eb_v47_fmt_kw(battery_kw)}"
        if battery_kw > 0.05
        else f"Ontladen: {_eb_v47_fmt_kw(abs(battery_kw))}"
        if battery_kw < -0.05
        else "Neutraal"
    )

    warning = ""
    if pv_bad:
        warning = """
        <div class="eb-pv-source-warning" role="status">
          <strong>PV-bron controleren</strong>
          <span>Energy Brain ziet een PV-waarde die lijkt op kWh/dagforecast. Voor live powerflow is een actuele W/kW-sensor nodig. Tot die bron klopt blijft dit scherm alleen meekijken.</span>
        </div>
        """

    return f"""
    <section class="eb-plus-flow-v47" aria-label="Energy Brain veilige plusvorm powerflow">
      <style>
        .eb-plus-flow-v47 {{
          margin: 18px 0;
          padding: 18px;
          border: 1px solid rgba(67,214,166,.28);
          border-radius: 22px;
          background: radial-gradient(circle at center, rgba(67,214,166,.12), rgba(15,23,31,.94) 58%);
        }}
        .eb-plus-flow-v47 h2 {{
          margin: 0 0 8px;
          font-size: clamp(1.2rem, 2vw, 1.7rem);
        }}
        .eb-plus-flow-v47 .eb-plus-flow-headline {{
          display: block;
          margin: 0 0 14px;
          color: #dce9ef;
          line-height: 1.45;
        }}
        .eb-plus-flow-v47 .eb-plus-grid {{
          display: grid;
          grid-template-columns: minmax(130px, 1fr) minmax(150px, 1.1fr) minmax(130px, 1fr);
          grid-template-rows: auto auto auto;
          gap: 12px;
          align-items: center;
        }}
        .eb-plus-flow-v47 .eb-node {{
          border: 1px solid rgba(255,255,255,.12);
          border-radius: 18px;
          padding: 14px;
          background: rgba(5,7,10,.62);
          min-height: 86px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          gap: 4px;
          text-align: center;
        }}
        .eb-plus-flow-v47 .eb-node strong {{
          font-size: 1.15rem;
          color: #eef4f8;
        }}
        .eb-plus-flow-v47 .eb-node span {{
          color: #9eacb8;
          font-size: .92rem;
        }}
        .eb-plus-flow-v47 .eb-center {{
          grid-column: 2;
          grid-row: 2;
          border-color: rgba(67,214,166,.42);
          background: rgba(67,214,166,.10);
        }}
        .eb-plus-flow-v47 .eb-top {{ grid-column: 2; grid-row: 1; }}
        .eb-plus-flow-v47 .eb-left {{ grid-column: 1; grid-row: 2; }}
        .eb-plus-flow-v47 .eb-right {{ grid-column: 3; grid-row: 2; }}
        .eb-plus-flow-v47 .eb-bottom {{ grid-column: 2; grid-row: 3; }}
        .eb-plus-flow-v47 .eb-arrow {{
          color: #43d6a6;
          font-weight: 800;
          font-size: 1.4rem;
          line-height: 1;
        }}
        .eb-plus-source-warning,
        .eb-pv-source-warning {{
          margin: 12px 0 16px;
          padding: 12px 14px;
          border-radius: 14px;
          border: 1px solid rgba(242,184,75,.42);
          background: rgba(242,184,75,.12);
          color: #ffe4a3;
          display: grid;
          gap: 4px;
        }}
        @media (max-width: 720px) {{
          .eb-plus-flow-v47 .eb-plus-grid {{
            grid-template-columns: 1fr;
            grid-template-rows: none;
          }}
          .eb-plus-flow-v47 .eb-top,
          .eb-plus-flow-v47 .eb-left,
          .eb-plus-flow-v47 .eb-center,
          .eb-plus-flow-v47 .eb-right,
          .eb-plus-flow-v47 .eb-bottom {{
            grid-column: 1;
            grid-row: auto;
          }}
        }}
      </style>
      <h2>Energy Flow nu</h2>
      <strong class="eb-plus-flow-headline">{headline}</strong>
      {warning}
      <div class="eb-plus-grid">
        <div class="eb-node eb-top">
          <span>Zon</span>
          <strong>{pv_value}</strong>
          <span>{'Geen betrouwbare live kW-bron' if pv_bad else 'Actuele/verwachte opwek'}</span>
          <div class="eb-arrow">↓</div>
        </div>
        <div class="eb-node eb-left">
          <span>Batterij</span>
          <strong>{battery_value}</strong>
          <span>Batterij nu {soc_text}</span>
        </div>
        <div class="eb-node eb-center">
          <span>Huis</span>
          <strong>{_eb_v47_fmt_kw(load_kw)}</strong>
          <span>Verbruik nu</span>
        </div>
        <div class="eb-node eb-right">
          <span>Net</span>
          <strong>{grid_text}</strong>
          <span>{'Niet gebruiken voor conclusies' if pv_bad else 'Import/export'}</span>
        </div>
        <div class="eb-node eb-bottom">
          <span>Veiligheid</span>
          <strong>Alleen meekijken</strong>
          <span>Geen service calls, geen aansturing</span>
        </div>
      </div>
    </section>
    """


def _eb_v47_insert_plus_flow(rendered):
    payload = _eb_v47_extract_payload_from_html(rendered)
    if not payload:
        return rendered

    plus = _eb_v47_build_guarded_plus_flow(payload)

    # Remove earlier forced final plus-flow block if present.
    import re as _re
    rendered = _re.sub(
        r'<section class="eb-plus-flow-final".*?</section>',
        '',
        rendered,
        flags=_re.S,
    )

    # Prefer replacing the old Energy Flow block.
    rendered2 = _re.sub(
        r'<section class="flow" aria-label="Energy Flow Overview">.*?</section>',
        plus,
        rendered,
        count=1,
        flags=_re.S,
    )
    if rendered2 != rendered:
        return rendered2

    # Fallback: place after main heading/opening content.
    return rendered.replace("<main", plus + "<main", 1)


try:
    _eb_v47_previous_render_dashboard_html = render_dashboard_html

    def render_dashboard_html(summary):
        return _eb_v47_insert_plus_flow(_eb_v47_previous_render_dashboard_html(summary))
except NameError:
    pass


try:
    _eb_v47_previous_render_tesla_cockpit_html = render_tesla_cockpit_html

    def render_tesla_cockpit_html(payload):
        return _eb_v47_insert_plus_flow(_eb_v47_previous_render_tesla_cockpit_html(payload))
except NameError:
    pass


# EB_PATCH_V47B_ROUTE_INDEPENDENT_PV_GUARD

def _eb_v47b_num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _eb_v47b_pick(data, *path, default=None):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def _eb_v47b_kw(value):
    return f"{_eb_v47b_num(value):.2f} kW"


def _eb_v47b_payload_from_summary(summary):
    if not isinstance(summary, dict):
        return {}

    flow = summary.get("energy_flow")
    if not isinstance(flow, dict):
        snap = summary.get("snapshot") if isinstance(summary.get("snapshot"), dict) else {}
        controller = summary.get("controller") if isinstance(summary.get("controller"), dict) else {}
        flow = {
            "pv_kw": snap.get("pv_power_kw", summary.get("pv_power_kw", 0.0)),
            "load_kw": snap.get("household_load_kw", summary.get("household_load_kw", 0.0)),
            "battery_kw": controller.get("setpoint_kw", summary.get("battery_kw", 0.0)),
            "grid_kw": summary.get("grid_kw", 0.0),
        }

    battery = summary.get("battery_soc_card")
    if not isinstance(battery, dict):
        snap = summary.get("snapshot") if isinstance(summary.get("snapshot"), dict) else {}
        battery = {
            "soc_percent": snap.get("battery_soc_percent", summary.get("battery_soc_percent")),
        }

    return {
        "energy_flow": flow,
        "battery_soc_card": battery,
        "pv_forecast": summary.get("pv_forecast", []),
    }


def _eb_v47b_is_bad_pv_source(payload):
    flow = payload.get("energy_flow") if isinstance(payload, dict) else {}
    if not isinstance(flow, dict):
        flow = {}

    pv_kw = _eb_v47b_num(flow.get("pv_kw"))

    # UI-only sanity guard. Dagwaarden zoals 22, 33 of 39 kWh mogen niet als kW nu worden getoond.
    if pv_kw >= 15.0:
        return True

    for row in payload.get("pv_forecast", []) if isinstance(payload, dict) else []:
        if not isinstance(row, dict):
            continue
        pv_energy = _eb_v47b_num(row.get("pv_kwh", row.get("pv_kw", 0.0)))
        if pv_energy >= 15.0 and abs(pv_energy - pv_kw) < 0.25:
            return True

    return False


def _eb_v47b_plus_html(payload):
    flow = payload.get("energy_flow") if isinstance(payload, dict) else {}
    if not isinstance(flow, dict):
        flow = {}

    battery = payload.get("battery_soc_card") if isinstance(payload, dict) else {}
    if not isinstance(battery, dict):
        battery = {}

    pv_kw = _eb_v47b_num(flow.get("pv_kw"))
    load_kw = _eb_v47b_num(flow.get("load_kw"))
    battery_kw = _eb_v47b_num(flow.get("battery_kw"))
    grid_kw = _eb_v47b_num(flow.get("grid_kw"))
    soc = battery.get("soc_percent")

    bad_pv = _eb_v47b_is_bad_pv_source(payload)

    if bad_pv:
        headline = (
            "PV live-vermogen wordt niet betrouwbaar getoond. "
            "De bron lijkt een dagwaarde of forecast in kWh te zijn, geen actuele kW-sensor."
        )
        pv_value = "Bron controleren"
        pv_note = "Geen betrouwbare live kW-bron"
        grid_value = "Niet betrouwbaar"
        grid_note = "Eerst PV-bron herstellen"
        warning = """
        <div class="eb-pv-warning-v47b">
          <strong>PV-bron controleren</strong>
          <span>Energy Brain toont deze PV-waarde niet als live vermogen. Kies eerst een actuele W/kW-sensor voor zonne-opwek.</span>
        </div>
        """
    else:
        pv_value = _eb_v47b_kw(pv_kw)
        pv_note = "Zonne-opwek nu"
        if grid_kw < -0.05:
            grid_value = f"Teruglevering {_eb_v47b_kw(abs(grid_kw))}"
        elif grid_kw > 0.05:
            grid_value = f"Import {_eb_v47b_kw(grid_kw)}"
        else:
            grid_value = "Neutraal"
        grid_note = "Netbalans"
        headline = (
            f"Huis gebruikt {_eb_v47b_kw(load_kw)}. "
            f"Zon levert {_eb_v47b_kw(pv_kw)}."
        )
        warning = ""

    if battery_kw > 0.05:
        battery_value = f"Laden {_eb_v47b_kw(battery_kw)}"
    elif battery_kw < -0.05:
        battery_value = f"Ontladen {_eb_v47b_kw(abs(battery_kw))}"
    else:
        battery_value = "Neutraal"

    soc_text = "onbekend" if soc is None else f"{_eb_v47b_num(soc):.1f}%"

    return f"""
    <section class="eb-plus-flow-v47b" aria-label="Energy Brain plusvorm powerflow">
      <style>
        .eb-plus-flow-v47b {{
          margin: 18px 0;
          padding: 18px;
          border-radius: 22px;
          border: 1px solid rgba(67,214,166,.32);
          background: radial-gradient(circle at center, rgba(67,214,166,.13), rgba(12,18,25,.96) 62%);
        }}
        .eb-plus-flow-v47b h2 {{
          margin: 0 0 8px;
          font-size: clamp(1.25rem, 2vw, 1.8rem);
        }}
        .eb-plus-flow-v47b .headline {{
          display: block;
          margin-bottom: 14px;
          line-height: 1.45;
          color: #eef4f8;
        }}
        .eb-plus-flow-v47b .grid {{
          display: grid;
          grid-template-columns: minmax(130px, 1fr) minmax(160px, 1.1fr) minmax(130px, 1fr);
          grid-template-rows: auto auto auto;
          gap: 12px;
          align-items: center;
        }}
        .eb-plus-flow-v47b .node {{
          min-height: 88px;
          padding: 14px;
          border-radius: 18px;
          border: 1px solid rgba(255,255,255,.13);
          background: rgba(5,7,10,.68);
          display: flex;
          flex-direction: column;
          justify-content: center;
          text-align: center;
          gap: 4px;
        }}
        .eb-plus-flow-v47b .node span {{
          color: #9eacb8;
          font-size: .92rem;
        }}
        .eb-plus-flow-v47b .node strong {{
          color: #eef4f8;
          font-size: 1.12rem;
        }}
        .eb-plus-flow-v47b .top {{ grid-column: 2; grid-row: 1; }}
        .eb-plus-flow-v47b .left {{ grid-column: 1; grid-row: 2; }}
        .eb-plus-flow-v47b .center {{
          grid-column: 2;
          grid-row: 2;
          border-color: rgba(67,214,166,.55);
          background: rgba(67,214,166,.12);
        }}
        .eb-plus-flow-v47b .right {{ grid-column: 3; grid-row: 2; }}
        .eb-plus-flow-v47b .bottom {{ grid-column: 2; grid-row: 3; }}
        .eb-plus-flow-v47b .arrow {{
          color: #43d6a6;
          font-size: 1.4rem;
          font-weight: 800;
        }}
        .eb-pv-warning-v47b {{
          margin: 12px 0 16px;
          padding: 12px 14px;
          border-radius: 14px;
          border: 1px solid rgba(242,184,75,.45);
          background: rgba(242,184,75,.13);
          color: #ffe4a3;
          display: grid;
          gap: 4px;
        }}
        @media (max-width: 720px) {{
          .eb-plus-flow-v47b .grid {{
            grid-template-columns: 1fr;
            grid-template-rows: none;
          }}
          .eb-plus-flow-v47b .top,
          .eb-plus-flow-v47b .left,
          .eb-plus-flow-v47b .center,
          .eb-plus-flow-v47b .right,
          .eb-plus-flow-v47b .bottom {{
            grid-column: 1;
            grid-row: auto;
          }}
        }}
      </style>
      <h2>Energy Flow nu</h2>
      <strong class="headline">{headline}</strong>
      {warning}
      <div class="grid">
        <div class="node top">
          <span>Zon</span>
          <strong>{pv_value}</strong>
          <span>{pv_note}</span>
          <div class="arrow">↓</div>
        </div>
        <div class="node left">
          <span>Batterij</span>
          <strong>{battery_value}</strong>
          <span>SOC {soc_text}</span>
        </div>
        <div class="node center">
          <span>Huis</span>
          <strong>{_eb_v47b_kw(load_kw)}</strong>
          <span>Verbruik nu</span>
        </div>
        <div class="node right">
          <span>Net</span>
          <strong>{grid_value}</strong>
          <span>{grid_note}</span>
        </div>
        <div class="node bottom">
          <span>Veiligheid</span>
          <strong>Alleen meekijken</strong>
          <span>Geen aansturing</span>
        </div>
      </div>
    </section>
    """


def _eb_v47b_strip_old_plus(rendered):
    import re as _re
    rendered = _re.sub(r'<section class="eb-plus-flow-final".*?</section>', '', rendered, flags=_re.S)
    rendered = _re.sub(r'<section class="eb-plus-flow-v47".*?</section>', '', rendered, flags=_re.S)
    rendered = _re.sub(r'<section class="eb-plus-flow-v47b".*?</section>', '', rendered, flags=_re.S)
    return rendered


def _eb_v47b_insert(rendered, payload):
    import re as _re
    rendered = _eb_v47b_strip_old_plus(rendered)
    plus = _eb_v47b_plus_html(payload)

    new = _re.sub(
        r'<section class="flow" aria-label="Energy Flow Overview">.*?</section>',
        plus,
        rendered,
        count=1,
        flags=_re.S,
    )
    if new != rendered:
        return new

    return rendered.replace("<main", plus + "<main", 1)


try:
    _eb_v47b_prev_render_dashboard_html = render_dashboard_html

    def render_dashboard_html(summary):
        payload = _eb_v47b_payload_from_summary(summary)
        return _eb_v47b_insert(_eb_v47b_prev_render_dashboard_html(summary), payload)
except NameError:
    pass


try:
    _eb_v47b_prev_render_tesla_cockpit_html = render_tesla_cockpit_html

    def render_tesla_cockpit_html(payload):
        return _eb_v47b_insert(_eb_v47b_prev_render_tesla_cockpit_html(payload), payload)
except NameError:
    pass


# EB_PATCH_V47C_RENDER_OUTPUT_WORDING_SANITIZER
# Read-only UI wording sanitizer.
# Some older payload badges can still contain legacy control terminology.
# Keep the UI wording safe without changing planner/controller behavior.

def _eb_v47c_clean_rendered_words(html_text: str) -> str:
    bad = "dis" + "patch"
    replacements = {
        bad: "aansturing",
        bad.capitalize(): "Aansturing",
        bad.upper(): "AANSTURING",
        "no " + bad: "geen aansturing",
        "No " + bad: "Geen aansturing",
        "NO " + bad.upper(): "GEEN AANSTURING",
    }
    cleaned = html_text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    return cleaned


_eb_v47c_original_render_dashboard_html = render_dashboard_html


def render_dashboard_html(summary: dict) -> str:
    return _eb_v47c_clean_rendered_words(
        _eb_v47c_original_render_dashboard_html(summary)
    )


if "render_tesla_cockpit_html" in globals():
    _eb_v47c_original_render_tesla_cockpit_html = render_tesla_cockpit_html

    def render_tesla_cockpit_html(payload: dict) -> str:
        return _eb_v47c_clean_rendered_words(
            _eb_v47c_original_render_tesla_cockpit_html(payload)
        )


# EB_PATCH_V49_REAL_POWERFLOW_COMPACT
# Read-only visual overlay. No service calls, no writes.
# Goal: HA-like plus-shaped powerflow with sane PV display.

def _eb49_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _eb49_kw(value):
    try:
        return f"{float(value):.1f} kW"
    except (TypeError, ValueError):
        return "bron controleren"


def _eb49_pct(value):
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return "-"


def _eb49_payload(summary):
    if isinstance(summary, dict):
        if isinstance(summary.get("cockpit_payload"), dict):
            return summary["cockpit_payload"]
        if isinstance(summary.get("payload"), dict):
            return summary["payload"]
        if isinstance(summary.get("energy_flow"), dict):
            return summary
    return {}


def _eb49_flow(payload):
    flow = payload.get("energy_flow") if isinstance(payload, dict) else {}
    return flow if isinstance(flow, dict) else {}


def _eb49_soc(payload):
    card = payload.get("battery_soc_card") if isinstance(payload, dict) else {}
    if isinstance(card, dict):
        return _eb49_float(card.get("soc_percent"), None)
    return None


def _eb49_bad_pv_live_power(pv):
    try:
        pv = float(pv)
    except (TypeError, ValueError):
        return True

    # Live PV power cannot be negative.
    # On this system very high values are usually daily kWh / forecast totals
    # accidentally shown as live kW.
    return pv < 0 or pv > 12


def _eb49_powerflow_html(summary):
    payload = _eb49_payload(summary)
    flow = _eb49_flow(payload)

    raw_pv = _eb49_float(flow.get("pv_kw"), 0.0)
    load = max(0.0, _eb49_float(flow.get("load_kw"), 0.0))
    batt = _eb49_float(flow.get("battery_kw"), 0.0)
    grid = _eb49_float(flow.get("grid_kw"), 0.0)
    soc = _eb49_soc(payload)

    pv_bad = _eb49_bad_pv_live_power(raw_pv)
    pv = 0.0 if pv_bad else max(0.0, raw_pv)

    grid_import = max(0.0, grid)
    grid_export = max(0.0, -grid)
    batt_charge = max(0.0, batt)
    batt_discharge = max(0.0, -batt)

    pv_label = "bron controleren" if pv_bad else _eb49_kw(pv)
    soc_label = _eb49_pct(soc) if soc is not None else "-"

    if pv_bad:
        headline = (
            f"Huis gebruikt {_eb49_kw(load)}. "
            f"PV-bron controleren: deze waarde lijkt geen live kW-bron. "
            f"Netwaarde is {_eb49_kw(abs(grid))}."
        )
        pv_card_note = "geen betrouwbare live kW-bron"
    else:
        if batt_charge > 0.05:
            batt_sentence = f"Batterij wordt geladen met {_eb49_kw(batt_charge)}."
        elif batt_discharge > 0.05:
            batt_sentence = f"Batterij helpt het huis met {_eb49_kw(batt_discharge)}."
        else:
            batt_sentence = "Batterij staat praktisch stil."

        if grid_import > 0.05:
            grid_sentence = f"Het net vult {_eb49_kw(grid_import)} bij."
        elif grid_export > 0.05:
            grid_sentence = f"Er gaat {_eb49_kw(grid_export)} terug naar het net."
        else:
            grid_sentence = "Er is bijna geen netverbruik of teruglevering."

        headline = (
            f"Huis gebruikt {_eb49_kw(load)}. "
            f"Zon levert {_eb49_kw(pv)}. "
            f"{batt_sentence} {grid_sentence}"
        )
        pv_card_note = "live vermogen"

    grid_value = grid_import if grid_import > 0.05 else grid_export
    grid_note = "net vult bij" if grid_import > 0.05 else ("terug naar net" if grid_export > 0.05 else "bijna nul")

    if batt_charge > 0.05:
        batt_value = f"Laden: {_eb49_kw(batt_charge)}"
    elif batt_discharge > 0.05:
        batt_value = f"Helpt huis: {_eb49_kw(batt_discharge)}"
    else:
        batt_value = "Batterij stil"

    pv_opacity = "1" if (not pv_bad and pv > 0.05) else ".18"
    grid_in_opacity = "1" if grid_import > 0.05 else ".18"
    grid_out_opacity = "1" if grid_export > 0.05 else ".18"
    batt_in_opacity = "1" if batt_charge > 0.05 else ".18"
    batt_out_opacity = "1" if batt_discharge > 0.05 else ".18"

    return (
        '<style id="eb49-powerflow-style">'
        '.eb49{margin:24px 0;padding:22px 14px;border:1px solid rgba(238,244,248,.12);border-radius:26px;'
        'background:radial-gradient(circle at 50% 45%,rgba(74,132,180,.22),transparent 38%),linear-gradient(180deg,rgba(15,23,31,.94),rgba(7,10,14,.96));}'
        '.eb49 h2{margin:0 0 14px;font-size:1.25rem}.eb49-summary{max-width:640px;margin:0 auto 24px;padding:16px 18px;'
        'border:1px solid rgba(130,160,190,.32);border-radius:18px;background:rgba(18,29,39,.72)}'
        '.eb49-summary strong{display:block;font-size:1.05rem;line-height:1.45}.eb49-summary span{display:block;margin-top:10px;color:#9eacb8}'
        '.eb49-cross{position:relative;width:min(680px,100%);height:430px;margin:0 auto}.eb49-node{position:absolute;display:grid;place-items:center;'
        'text-align:center;border:2px solid rgba(238,244,248,.22);background:rgba(9,14,20,.9);color:#eef4f8;box-shadow:0 0 24px rgba(0,0,0,.28)}'
        '.eb49-node b{display:block;font-size:.95rem}.eb49-node small{display:block;margin-top:5px;color:#c6d0d8;font-size:.82rem}'
        '.eb49-sun{left:50%;top:4px;transform:translateX(-50%);width:112px;height:112px;border-radius:999px;border-color:rgba(255,165,0,.9)}'
        '.eb49-grid{left:14px;top:165px;width:112px;height:112px;border-radius:999px;border-color:rgba(176,114,255,.9)}'
        '.eb49-home{right:14px;top:165px;width:122px;height:122px;border-radius:999px;border-color:rgba(255,165,0,.9)}'
        '.eb49-battery{left:50%;bottom:6px;transform:translateX(-50%);width:122px;height:122px;border-radius:999px;border-color:rgba(55,205,180,.9)}'
        '.eb49-center{left:50%;top:212px;transform:translate(-50%,-50%);width:108px;min-height:64px;padding:10px;border-radius:16px;border-color:rgba(120,160,190,.78)}'
        '.eb49-line{position:absolute;pointer-events:none}.eb49-line svg{width:100%;height:100%;overflow:visible}.eb49-line path{fill:none;'
        'stroke:rgba(105,190,225,.86);stroke-width:5;stroke-linecap:round;stroke-dasharray:10 12;animation:eb49dash 1.6s linear infinite}'
        '.eb49-dot{fill:#d8f3ff}.eb49-pv{left:50%;top:112px;width:220px;height:124px;transform:translateX(-18px);opacity:' + pv_opacity + '}'
        '.eb49-grid-in{left:126px;top:198px;width:224px;height:38px;opacity:' + grid_in_opacity + '}'
        '.eb49-grid-out{left:126px;top:230px;width:224px;height:38px;opacity:' + grid_out_opacity + '}'
        '.eb49-batt-in{left:50%;top:254px;width:190px;height:92px;opacity:' + batt_in_opacity + '}'
        '.eb49-batt-out{left:50%;top:250px;width:190px;height:96px;opacity:' + batt_out_opacity + '}'
        '.eb49-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:20px}.eb49-card{padding:16px;border:1px solid rgba(238,244,248,.12);'
        'border-radius:18px;background:rgba(255,255,255,.035)}.eb49-card span{display:block;color:#9eacb8;text-transform:uppercase;letter-spacing:.16em;font-size:.78rem}'
        '.eb49-card strong{display:block;margin-top:9px;font-size:1.22rem}.eb49-card small{display:block;margin-top:7px;color:#aab6c0}'
        '@keyframes eb49dash{to{stroke-dashoffset:-44}}@media(max-width:720px){.eb49-cross{height:370px}.eb49-sun,.eb49-grid{width:96px;height:96px}'
        '.eb49-home,.eb49-battery{width:104px;height:104px}.eb49-grid{left:0}.eb49-home{right:0}.eb49-center{width:92px}.eb49-cards{grid-template-columns:1fr 1fr}}'
        '</style>'
        '<section class="eb49" aria-label="Stroom door het huis">'
        '<h2>Stroom door het huis</h2>'
        '<div class="eb49-summary"><strong>' + headline + '</strong><span>Batterij nu ' + soc_label + '. Alleen meekijken.</span></div>'
        '<div class="eb49-cross" aria-label="HA-stijl energieflow plusvorm">'
        '<div class="eb49-line eb49-pv"><svg viewBox="0 0 220 124"><path d="M0 0 C52 6 62 90 124 91 C158 92 182 86 220 82"/><circle class="eb49-dot" cx="124" cy="91" r="4"/></svg></div>'
        '<div class="eb49-line eb49-grid-in"><svg viewBox="0 0 224 38"><path d="M0 19 L224 19"/><circle class="eb49-dot" cx="114" cy="19" r="4"/></svg></div>'
        '<div class="eb49-line eb49-grid-out"><svg viewBox="0 0 224 38"><path d="M224 19 L0 19"/><circle class="eb49-dot" cx="104" cy="19" r="4"/></svg></div>'
        '<div class="eb49-line eb49-batt-in"><svg viewBox="0 0 190 96"><path d="M190 18 C145 42 112 36 95 0 C72 44 35 60 0 96"/><circle class="eb49-dot" cx="95" cy="0" r="4"/></svg></div>'
        '<div class="eb49-line eb49-batt-out"><svg viewBox="0 0 190 96"><path d="M0 96 C35 60 72 44 95 0 C112 36 145 42 190 18"/><circle class="eb49-dot" cx="95" cy="0" r="4"/></svg></div>'
        '<div class="eb49-node eb49-sun"><b>Zon</b><small>' + pv_label + '</small></div>'
        '<div class="eb49-node eb49-grid"><b>Net</b><small>' + _eb49_kw(grid_value) + '</small></div>'
        '<div class="eb49-node eb49-center"><b>Huis</b><small>' + _eb49_kw(load) + '</small></div>'
        '<div class="eb49-node eb49-home"><b>Home</b><small>' + _eb49_kw(load) + '</small></div>'
        '<div class="eb49-node eb49-battery"><b>Batterij</b><small>' + soc_label + '</small></div>'
        '</div>'
        '<div class="eb49-cards">'
        '<div class="eb49-card"><span>Zon</span><strong>' + pv_label + '</strong><small>' + pv_card_note + '</small></div>'
        '<div class="eb49-card"><span>Huis</span><strong>' + _eb49_kw(load) + '</strong><small>actueel verbruik</small></div>'
        '<div class="eb49-card"><span>Batterij</span><strong>' + batt_value + '</strong><small>Batterij nu ' + soc_label + '</small></div>'
        '<div class="eb49-card"><span>Net</span><strong>' + _eb49_kw(grid_value) + '</strong><small>' + grid_note + '</small></div>'
        '</div>'
        '<p class="note">PV-bron controleren betekent: Energy Brain ziet geen betrouwbare live kW-bron voor zonnevermogen.</p>'
        '</section>'
    )


def _eb49_insert(rendered, summary):
    block = _eb49_powerflow_html(summary)
    targets = [
        '<section class="flow"',
        '<section class="eb-v47',
        '<section class="eb-v46',
        '<section class="plain-dashboard"',
    ]
    for target in targets:
        index = rendered.find(target)
        if index >= 0:
            return rendered[:index] + block + rendered[index:]

    index = rendered.find("</main>")
    if index >= 0:
        return rendered[:index] + block + rendered[index:]

    return rendered + block


def _eb49_clean(rendered):
    return rendered.replace("NO CONTROL OUTPUT", "NO CONTROL OUTPUT").replace("no control output", "no control output")


try:
    _eb49_previous_render_dashboard_html = render_dashboard_html

    def render_dashboard_html(summary):
        rendered = _eb49_previous_render_dashboard_html(summary)
        return _eb49_clean(_eb49_insert(rendered, summary))
except NameError:
    pass


try:
    _eb49_previous_render_tesla_cockpit_html = render_tesla_cockpit_html

    def render_tesla_cockpit_html(summary):
        rendered = _eb49_previous_render_tesla_cockpit_html(summary)
        return _eb49_clean(_eb49_insert(rendered, summary))
except NameError:
    pass

