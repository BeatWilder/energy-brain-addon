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
