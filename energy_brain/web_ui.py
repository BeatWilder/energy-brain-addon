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
    rows = [
        ("status", summary.get("status")),
        ("valid_cycle", summary.get("valid_cycle")),
        ("message", summary.get("message")),
        ("mode", summary.get("mode")),
        ("controller.approved", _get(summary, "controller", "approved")),
        ("controller.execute", _get(summary, "controller", "execute")),
        ("execution.attempted", _get(summary, "execution", "attempted")),
        ("snapshot.battery_soc_percent", _get(summary, "snapshot", "battery_soc_percent")),
        ("snapshot.pv_power_kw", _get(summary, "snapshot", "pv_power_kw")),
        ("snapshot.household_load_kw", _get(summary, "snapshot", "household_load_kw")),
        ("snapshot.grid_price", _get(summary, "snapshot", "grid_price")),
        ("plan.valid", _get(summary, "plan", "valid")),
        ("plan.expected_cost", _get(summary, "plan", "expected_cost")),
        ("plan.baseline_cost", _get(summary, "plan", "baseline_cost")),
        ("plan.delta_vs_baseline", _get(summary, "plan", "delta_vs_baseline")),
        ("controller.setpoint_kw", _get(summary, "controller", "setpoint_kw")),
        ("min_soc_percent", _get(summary, "plan", "min_soc_percent")),
        ("max_soc_percent", _get(summary, "plan", "max_soc_percent")),
    ]
    step_rows = "\n".join(_render_step_row(step) for step in _list(_get(summary, "plan", "steps")))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain UI</title>
  <style>
    body {{
      margin: 0;
      background: #f7f7f4;
      color: #1d1f23;
      font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 16px;
      letter-spacing: 0;
    }}
    section {{
      margin-top: 24px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      border: 1px solid #d8d9d6;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid #e7e7e3;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #ecefeb;
      font-weight: 650;
    }}
    .warning {{
      color: #8a4b00;
      font-weight: 650;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Energy Brain UI</h1>
    <section>
      <h2>Latest Cycle</h2>
      <table>
        <tbody>
          {_render_summary_rows(rows)}
        </tbody>
      </table>
    </section>
    <section>
      <h2>First 24 Planner Steps</h2>
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
        rendered.append(f"<tr><th>{_escape(label)}</th><td{css_class}>{display}</td></tr>")
    return "\n          ".join(rendered)


def _render_step_row(step: Any) -> str:
    step = _dict(step)
    cells = [
        step.get("index"),
        step.get("battery_setpoint_kw"),
        step.get("soc_percent"),
        step.get("reason"),
    ]
    return "<tr>" + "".join(f"<td>{_display(value)}</td>" for value in cells) + "</tr>"


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
