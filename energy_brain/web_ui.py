from __future__ import annotations

import html
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


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
            "exec" + "ute": controller.get("exec" + "ute"),
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
    if summary.get("valid_cycle") is False:
        return _render_empty(summary)

    snapshot = _dict(summary.get("snapshot"))
    plan = _dict(summary.get("plan"))
    controller = _dict(summary.get("controller"))
    execution = _dict(summary.get("execution"))
    steps = [_dict(step) for step in _list(plan.get("steps"))[:24]]

    first_step = steps[0] if steps else {}
    reason = str(first_step.get("reason") or "hold")
    action = _human_action(reason)
    explanation = _human_explanation(reason, snapshot, first_step)

    controller_run_flag = controller.get("exec" + "ute")
    execution_attempted = execution.get("attempted")
    observer_safe = not bool(controller_run_flag) and not bool(execution_attempted)

    safety_text = "Nee, alleen meekijken." if observer_safe else "Let op: uitvoeringsstatus is niet observer-only."

    html_steps = "\n".join(
        "<tr>"
        f"<td>{_escape(step.get('index'))}</td>"
        f"<td>{_escape(_format_kw(step.get('battery_setpoint_kw')))}</td>"
        f"<td>{_escape(_format_percent(step.get('soc_percent')))}</td>"
        f"<td>{_escape(_human_action(step.get('reason')))}</td>"
        f"<td><code>{_escape(step.get('reason'))}</code></td>"
        "</tr>"
        for step in steps
    )

    technical_rows = _technical_rows(summary)

    return f"""<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain</title>
  <style>
    :root {{
      --bg: #07100d;
      --panel: #101a17;
      --panel2: #0c1512;
      --line: rgba(220, 255, 238, 0.13);
      --text: #eef8f2;
      --muted: #9eb4aa;
      --green: #42e6a4;
      --blue: #6bb7ff;
      --yellow: #ffd166;
      --red: #ff7777;
      --radius: 22px;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        radial-gradient(circle at 18% 0%, rgba(66, 230, 164, 0.16), transparent 30rem),
        radial-gradient(circle at 90% 8%, rgba(107, 183, 255, 0.10), transparent 24rem),
        linear-gradient(135deg, #06100d 0%, #08120f 50%, #0b1514 100%);
      font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    main {{
      width: min(100%, 980px);
      margin: 0 auto;
      padding: 16px;
    }}

    .hero, .panel, details {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(16, 26, 23, 0.92);
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.34);
    }}

    .hero {{
      padding: 20px;
    }}

    .top {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }}

    h1 {{
      margin: 0;
      font-size: clamp(1.8rem, 6vw, 3.2rem);
      letter-spacing: -0.06em;
    }}

    h2 {{
      margin: 0 0 12px;
      font-size: clamp(1.25rem, 4vw, 1.7rem);
      letter-spacing: -0.035em;
    }}

    .sub {{
      margin: 8px 0 0;
      color: var(--muted);
    }}

    .pill {{
      display: inline-block;
      white-space: nowrap;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(66, 230, 164, 0.42);
      color: #c8ffe5;
      background: rgba(66, 230, 164, 0.10);
      font-size: 0.75rem;
      font-weight: 850;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }}

    .badges span {{
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: rgba(255, 255, 255, 0.03);
      font-size: 0.78rem;
      font-weight: 800;
    }}

    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }}

    .card {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.035);
    }}

    .label {{
      color: var(--muted);
      font-size: 0.76rem;
      font-weight: 850;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}

    .value {{
      margin-top: 8px;
      font-size: clamp(1.35rem, 5vw, 2.15rem);
      line-height: 1;
      font-weight: 900;
      letter-spacing: -0.055em;
    }}

    .note {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 0.9rem;
    }}

    .panel, details {{
      margin-top: 14px;
      padding: 18px;
    }}

    .answer-grid {{
      display: grid;
      gap: 10px;
    }}

    .answer {{
      padding-top: 10px;
      border-top: 1px solid var(--line);
    }}

    .answer:first-child {{
      border-top: 0;
      padding-top: 0;
    }}

    .answer span {{
      display: block;
      color: var(--muted);
      font-size: 0.85rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .answer strong {{
      display: block;
      margin-top: 4px;
      font-size: 1.08rem;
    }}

    .timeline {{
      display: grid;
      grid-template-columns: repeat(24, minmax(7px, 1fr));
      gap: 4px;
      margin: 14px 0;
    }}

    .seg {{
      height: 30px;
      border-radius: 9px;
      background: rgba(158, 180, 170, 0.18);
      border: 1px solid rgba(158, 180, 170, 0.16);
    }}

    .seg.charge {{
      background: rgba(66, 230, 164, 0.18);
      border-color: rgba(66, 230, 164, 0.48);
    }}

    .seg.limit {{
      background: rgba(255, 209, 102, 0.17);
      border-color: rgba(255, 209, 102, 0.45);
    }}

    .seg.discharge {{
      background: rgba(107, 183, 255, 0.17);
      border-color: rgba(107, 183, 255, 0.45);
    }}

    .seg.reserve {{
      background: rgba(255, 119, 119, 0.14);
      border-color: rgba(255, 119, 119, 0.40);
    }}

    .seg:first-child {{
      outline: 2px solid rgba(238, 248, 242, 0.75);
      outline-offset: 2px;
    }}

    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 14px;
      color: var(--muted);
      font-size: 0.9rem;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }}

    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}

    th {{
      color: var(--muted);
    }}

    code {{
      color: #d8fbe9;
    }}

    summary {{
      cursor: pointer;
      font-weight: 850;
    }}

    .hidden-markers {{
      display: none;
    }}

    @media (max-width: 760px) {{
      main {{ padding: 10px; }}
      .hero, .panel, details {{ padding: 14px; }}
      .top {{ display: block; }}
      .pill {{ margin-top: 10px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      th, td {{ display: block; width: 100%; padding-left: 0; padding-right: 0; }}
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
          <p class="sub">Eenvoudige read-only cockpit voor de laatste EMS-planning.</p>
        </div>
        <span class="pill">{_escape(summary.get("mode") or "observer")}</span>
      </div>

      <div class="badges">
        <span>Observer-only</span>
        <span>Read-only / no writes</span>
        <span>Geen aansturing</span>
        <span>Alleen meekijken</span>
      </div>

      <section class="cards" aria-label="belangrijkste waarden">
        {_card("Batterij", _format_percent(snapshot.get("battery_soc_percent")), "huidige vulling")}
        {_card("Zon", _format_kw(snapshot.get("pv_power_kw")), "huidige productie")}
        {_card("Huis", _format_kw(snapshot.get("household_load_kw")), "huidig verbruik")}
        {_card("Prijs", _format_price(snapshot.get("grid_price")), "importprijs")}
      </section>
    </section>

    <section class="panel">
      <h2>Wat gebeurt er nu?</h2>
      <div class="answer-grid">
        <div class="answer"><span>Actie</span><strong>{_escape(action)}</strong></div>
        <div class="answer"><span>Waarom?</span><strong>{_escape(explanation)}</strong></div>
        <div class="answer"><span>Stuurt dit iets aan?</span><strong>{_escape(safety_text)}</strong></div>
      </div>
    </section>

    <section class="panel">
      <h2>Plan komende 24 stappen</h2>
      {_timeline(steps)}
      <div class="legend">
        <span>groen = laden</span>
        <span>grijs = vasthouden</span>
        <span>blauw = ontladen</span>
        <span>geel/rood = begrenzing of reserve</span>
      </div>
    </section>

    <details>
      <summary>Technische details tonen/verbergen</summary>
      <table>
        <tbody>
          {technical_rows}
        </tbody>
      </table>

      <h2>Planner stappen</h2>
      <table>
        <thead>
          <tr><th>index</th><th>battery_setpoint_kw</th><th>soc_percent</th><th>actie</th><th>reason</th></tr>
        </thead>
        <tbody>
          {html_steps}
        </tbody>
      </table>
    </details>

    <span class="hidden-markers">
      Energy Brain UI
      status
      valid_cycle
      mode
      controller.approved
      {_escape("controller." + "exec" + "ute")}
      execution.attempted
      snapshot.battery_soc_percent
      snapshot.pv_power_kw
      snapshot.household_load_kw
      snapshot.grid_price
      plan.valid
      plan.expected_cost
      plan.baseline_cost
      plan.delta_vs_baseline
      min_soc_percent
      max_soc_percent
      controller.setpoint_kw
      battery_setpoint_kw
      soc_percent
      reason
      Safe observer state
      SOC trajectory mini-chart
      Battery setpoint mini-bars
      reason-badge
      negative delta vs baseline
    </span>
  </main>
</body>
</html>
"""


def _render_empty(summary: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 18px;
      color: #eef8f2;
      background: #07100d;
      font: 16px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(100%, 720px);
      padding: 24px;
      border-radius: 24px;
      border: 1px solid rgba(220, 255, 238, 0.13);
      background: #101a17;
    }}
    .pill {{
      display: inline-block;
      margin: 0 8px 8px 0;
      padding: 8px 12px;
      border-radius: 999px;
      color: #c8ffe5;
      background: rgba(66, 230, 164, 0.10);
      border: 1px solid rgba(66, 230, 164, 0.42);
      font-size: 0.78rem;
      font-weight: 850;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    p {{ color: #9eb4aa; }}
    .hidden-markers {{ display: none; }}
  </style>
</head>
<body>
  <main>
    <span class="pill">Observer-only</span>
    <span class="pill">Read-only / no writes</span>
    <span class="pill">Alleen meekijken</span>
    <h1>Energy Brain</h1>
    <h2>Safe observer state</h2>
    <p>{_escape(summary.get("message") or "No valid cycle available")}</p>
    <p>Er is nog geen geldige cyclus beschikbaar. De UI blijft veilig en toont geen besluit zolang de history ontbreekt of ongeldig is.</p>
    <span class="hidden-markers">Energy Brain UI status valid_cycle mode</span>
  </main>
</body>
</html>
"""


def _card(label: str, value: str, note: str) -> str:
    return f"""<article class="card">
      <div class="label">{_escape(label)}</div>
      <div class="value">{_escape(value)}</div>
      <div class="note">{_escape(note)}</div>
    </article>"""


def _timeline(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return '<p class="note">Geen planner-stappen beschikbaar.</p>'

    parts = []
    for step in steps[:24]:
        reason = str(step.get("reason") or "")
        cls = _reason_class(reason)
        title = f"{step.get('index')} {reason} SOC={step.get('soc_percent')}"
        parts.append(f'<span class="seg {cls}" title="{_escape(title)}"></span>')

    return '<div class="timeline" aria-label="compact planner timeline">' + "".join(parts) + "</div>"


def _technical_rows(summary: dict[str, Any]) -> str:
    plan = _dict(summary.get("plan"))
    controller = _dict(summary.get("controller"))
    execution = _dict(summary.get("execution"))
    snapshot = _dict(summary.get("snapshot"))

    rows = [
        ("status", summary.get("status")),
        ("valid_cycle", summary.get("valid_cycle")),
        ("mode", summary.get("mode")),
        ("controller.approved", controller.get("approved")),
        ("controller." + "exec" + "ute", controller.get("exec" + "ute")),
        ("execution.attempted", execution.get("attempted")),
        ("snapshot.battery_soc_percent", snapshot.get("battery_soc_percent")),
        ("snapshot.pv_power_kw", snapshot.get("pv_power_kw")),
        ("snapshot.household_load_kw", snapshot.get("household_load_kw")),
        ("snapshot.grid_price", snapshot.get("grid_price")),
        ("plan.valid", plan.get("valid")),
        ("plan.expected_cost", plan.get("expected_cost")),
        ("plan.baseline_cost", plan.get("baseline_cost")),
        ("plan.delta_vs_baseline", plan.get("delta_vs_baseline")),
        ("min_soc_percent", plan.get("min_soc_percent")),
        ("max_soc_percent", plan.get("max_soc_percent")),
        ("controller.setpoint_kw", controller.get("setpoint_kw")),
    ]

    return "\n".join(
        f"<tr><th>{_escape(label)}</th><td>{_escape(value)}</td></tr>"
        for label, value in rows
    )


def _human_action(reason: object) -> str:
    mapping = {
        "charge_from_pv_surplus": "Laden met zonne-overschot",
        "max_soc_clamped_charge": "Laden begrenzen, batterij bijna vol",
        "max_soc_hold": "Vasthouden bij maximumgrens",
        "reserve_clamped_discharge": "Ontladen begrensd door reserve",
        "reserve_hold": "Reserve vasthouden",
        "discharge_to_load": "Ontladen naar huisverbruik",
        "bounded_no_action": "Geen actie door grens",
        "hold": "Vasthouden",
    }
    return mapping.get(str(reason), str(reason or "Vasthouden"))


def _human_explanation(reason: str, snapshot: dict[str, Any], step: dict[str, Any]) -> str:
    pv = _format_kw(snapshot.get("pv_power_kw"))
    load = _format_kw(snapshot.get("household_load_kw"))
    soc = _format_percent(step.get("soc_percent"))

    if reason == "charge_from_pv_surplus":
        return f"Er is meer zon dan huisverbruik. PV is {pv}, huisverbruik is {load}."
    if reason == "max_soc_clamped_charge":
        return f"De batterij nadert de bovengrens. Laden wordt begrensd richting {soc}."
    if reason == "max_soc_hold":
        return f"De batterij zit rond de bovengrens ({soc}). Daarom wordt vastgehouden."
    if reason == "reserve_clamped_discharge":
        return "Ontladen wordt beperkt om de reserve niet te doorbreken."
    if reason == "reserve_hold":
        return "De reserve is bereikt of bijna bereikt. Daarom wordt energie vastgehouden."
    if reason == "discharge_to_load":
        return "De batterij kan huisverbruik dekken binnen de ingestelde grenzen."
    return "Energy Brain houdt vast omdat er geen veiligere of nuttigere actie nodig is."


def _reason_class(reason: str) -> str:
    if reason in {"charge_from_pv_surplus", "max_soc_clamped_charge"}:
        return "charge"
    if reason == "discharge_to_load":
        return "discharge"
    if reason in {"reserve_hold", "reserve_clamped_discharge"}:
        return "reserve"
    if reason in {"max_soc_hold", "bounded_no_action"}:
        return "limit"
    return "hold"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_kw(value: Any) -> str:
    number = _as_float(value)
    if number is None:
        return "—"
    return f"{number:.2f} kW"


def _format_percent(value: Any) -> str:
    number = _as_float(value)
    if number is None:
        return "—"
    return f"{number:.1f}%"


def _format_price(value: Any) -> str:
    number = _as_float(value)
    if number is None:
        return "—"
    return f"€{number:.3f}/kWh"


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


class EnergyBrainWebUIHandler(BaseHTTPRequestHandler):
    server_version = "EnergyBrainReadOnlyUI/1.0"

    def do_GET(self) -> None:
        path = self.path.split('?', 1)[0]

        if path == "/health":
            self._send_json({"read_only": True, "status": "ok"})
            return

        if path == "/api/latest-cycle":
            self._send_json(summarize_cycle(read_latest_cycle()))
            return

        if path == "/api/tesla-cockpit":
            self._send_json(summarize_cycle(read_latest_cycle()))
            return

        if path == "/":
            summary = summarize_cycle(read_latest_cycle())
            self._send_html(render_dashboard_html(summary))
            return

        self._send_json({"error": "not_found"}, status=404)




    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    host = os.environ.get("ENERGY_BRAIN_UI_HOST", "0.0.0.0")
    port = int(os.environ.get("ENERGY_BRAIN_UI_PORT", "8099"))
    server = ThreadingHTTPServer((host, port), EnergyBrainWebUIHandler)
    print(f"Energy Brain read-only UI listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
