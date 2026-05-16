from __future__ import annotations

import os

import html
import json
from pathlib import Path
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


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
        if self.path == "/health":
            self._send_json({"status": "ok", "read_only": True})
            return

        if self.path == "/api/latest-cycle":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            self._send_json(summary)
            return

        if self.path == "/":
            cycle = read_latest_cycle()
            summary = summarize_cycle(cycle)
            html = render_dashboard_html(summary)
            self._send_response(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return

        self._send_json({"status": "not_found", "read_only": True}, status=404)

    def do_POST(self) -> None:
        self._send_json({"status": "method_not_allowed", "read_only": True}, status=405)

    def do_PUT(self) -> None:
        self._send_json({"status": "method_not_allowed", "read_only": True}, status=405)

    def do_PATCH(self) -> None:
        self._send_json({"status": "method_not_allowed", "read_only": True}, status=405)

    def do_DELETE(self) -> None:
        self._send_json({"status": "method_not_allowed", "read_only": True}, status=405)

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
